import dataclasses
import importlib
import logging
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from shutil import rmtree

from algokit_utils.config import config
from dotenv import load_dotenv

config.configure(debug=True, trace_all=False)

# Set up logging and load environment variables.
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)-10s: %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Loading .env")
load_dotenv()

# Determine the root path based on this file's location.
root_path = Path(__file__).parent
src_artifact_path = root_path.parent / "src" / "artifacts"
canonical_src_contract_name = "d_asa"
canonical_src_app_spec_name = "DASA.arc56.json"
canonical_src_client_name = "dasa_client.py"
canonical_src_avm_client_name = "dasa_avm_client.py"
generated_artifacts_init = '"""Generated client artifacts."""\n'

# ----------------------- Contract Configuration ----------------------- #


@dataclasses.dataclass
class SmartContract:
    path: Path
    name: str
    deploy: Callable[[], None] | None = None


def import_contract(folder: Path) -> Path:
    """Imports the contract from a folder if it exists."""
    contract_path = folder / "contract.py"
    if contract_path.exists():
        return contract_path
    else:
        raise Exception(f"Contract not found in {folder}")


def import_deploy_if_exists(folder: Path) -> Callable[[], None] | None:
    """Imports the deploy function from a folder if it exists."""
    try:
        module_name = f"{folder.parent.name}.{folder.name}.deploy_config"
        deploy_module = importlib.import_module(module_name)
        return deploy_module.deploy  # type: ignore[no-any-return, misc]
    except ImportError:
        return None


def has_contract_file(directory: Path) -> bool:
    """Checks whether the directory contains a contract.py file."""
    return (directory / "contract.py").exists()


# Use the current directory (root_path) as the base for contract folders and exclude
# folders that start with '_' (internal helpers).
contracts: list[SmartContract] = [
    SmartContract(
        path=import_contract(folder),
        name=folder.name,
        deploy=import_deploy_if_exists(folder),
    )
    for folder in root_path.iterdir()
    if folder.is_dir() and has_contract_file(folder) and not folder.name.startswith("_")
]

# -------------------------- Build Logic -------------------------- #

deployment_extension = "py"


def _to_snake_case(name: str) -> str:
    """Converts CamelCase or acronym-heavy names to snake_case."""
    if name.isupper():
        return name.lower()

    first_pass = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    second_pass = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first_pass)
    return second_pass.lower()


def _get_client_output_dir(output_dir: Path, contract_name: str) -> Path:
    """Returns where generated clients should be written for a contract."""
    if contract_name == canonical_src_contract_name:
        return src_artifact_path
    return output_dir


def _get_typed_client_output_path(
    target_dir: Path,
    contract_name: str,
    app_spec_contract_name: str,
    deployment_extension: str,
) -> Path:
    """Constructs the output path for the generated client file."""
    if contract_name == canonical_src_contract_name:
        return target_dir / canonical_src_client_name

    base_name = (
        f"{_to_snake_case(app_spec_contract_name)}_client"
        if deployment_extension == "py"
        else f"{app_spec_contract_name}Client"
    )
    return target_dir / f"{base_name}.{deployment_extension}"


def _get_avm_client_output_path(
    target_dir: Path, contract_name: str, app_spec_contract_name: str
) -> Path:
    """Constructs the output path for the generated AVM client file."""
    if contract_name == canonical_src_contract_name:
        return target_dir / canonical_src_avm_client_name

    return target_dir / f"{_to_snake_case(app_spec_contract_name)}_avm_client.py"


def _get_app_spec_path(output_dir: Path, contract_name: str) -> Path | None:
    """Gets the canonical ARC-56 path for a contract if it exists."""
    if contract_name == canonical_src_contract_name:
        app_spec_path = src_artifact_path / canonical_src_app_spec_name
        return app_spec_path if app_spec_path.exists() else None

    return next(
        (
            file
            for file in output_dir.iterdir()
            if file.is_file() and file.suffixes == [".arc56", ".json"]
        ),
        None,
    )


def _reset_src_artifacts(contract_name: str) -> None:
    """Clears and recreates the canonical generated artifact package."""
    if contract_name != canonical_src_contract_name:
        return

    if src_artifact_path.exists():
        rmtree(src_artifact_path)
    src_artifact_path.mkdir(parents=True, exist_ok=True)
    (src_artifact_path / "__init__.py").write_text(
        generated_artifacts_init, encoding="utf-8"
    )


def _sync_src_artifacts(output_dir: Path, contract_name: str) -> Path | None:
    """Moves the canonical D-ASA artifacts into src/artifacts."""
    if contract_name != canonical_src_contract_name:
        return None

    src_artifact_path.mkdir(parents=True, exist_ok=True)

    app_spec_path = output_dir / canonical_src_app_spec_name
    if not app_spec_path.exists():
        raise Exception("Could not build contract, DASA.arc56.json file not found")

    canonical_app_spec_path = src_artifact_path / canonical_src_app_spec_name
    app_spec_path.replace(canonical_app_spec_path)
    return canonical_app_spec_path


def build(output_dir: Path, contract_name: str, contract_path: Path) -> Path:
    """
    Builds the contract by exporting (compiling) its source and generating a client.
    If the output directory already exists, it is cleared.
    """
    output_dir = output_dir.resolve()
    if output_dir.exists():
        rmtree(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    _reset_src_artifacts(contract_name)
    logger.info(f"Exporting {contract_path} to {output_dir}")

    build_result = subprocess.run(
        [
            "algokit",
            "--no-color",
            "compile",
            "python",
            str(contract_path.resolve()),
            f"--out-dir={output_dir}",
            "--output-source-map",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if build_result.stdout:
        print(build_result.stdout)

    if build_result.returncode:
        raise Exception(f"Could not build contract:\n{build_result.stdout}")

    # Look for arc56.json files and generate the client based on them.
    app_spec_file_names: list[str] = [
        file.name for file in output_dir.glob("*.arc56.json")
    ]

    client_file: str | None = None
    if not app_spec_file_names:
        logger.warning(
            "No '*.arc56.json' file found (likely a logic signature being compiled). Skipping client generation."
        )
    else:
        target_dir = _get_client_output_dir(output_dir, contract_name)
        target_dir.mkdir(exist_ok=True, parents=True)

        # Generate Python App Clients (off-chain)
        for file_name in app_spec_file_names:
            client_file = file_name
            print(file_name)
            app_spec_contract_name = file_name.removesuffix(".arc56.json")
            client_output_path = _get_typed_client_output_path(
                target_dir,
                contract_name,
                app_spec_contract_name,
                deployment_extension,
            )
            generate_result = subprocess.run(
                [
                    "algokit",
                    "generate",
                    "client",
                    str(output_dir),
                    "--output",
                    str(client_output_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            if generate_result.stdout:
                print(generate_result.stdout)

            if generate_result.returncode:
                if "No such command" in generate_result.stdout:
                    raise Exception(
                        "Could not generate typed client, requires AlgoKit 2.0.0 or later. Please update AlgoKit"
                    )
                else:
                    raise Exception(
                        f"Could not generate typed client:\n{generate_result.stdout}"
                    )

        # Generate Python AVM Clients (on-chain)
        for file_name in app_spec_file_names:
            app_spec_contract_name = file_name.removesuffix(".arc56.json")
            logger.info(f"Generating AVM Client (on-chain) for {file_name}")

            puyapy_result = subprocess.run(
                [
                    "poetry",
                    "run",
                    "puyapy-clientgen",
                    str(output_dir / file_name),
                    "--out-dir",
                    str(target_dir),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            if puyapy_result.stdout:
                print(puyapy_result.stdout)

            if puyapy_result.returncode:
                raise Exception(
                    f"Could not generate client with puyapy-clientgen:\n{puyapy_result.stdout}"
                )

            generated_file = target_dir / f"client_{app_spec_contract_name}.py"
            desired_file = _get_avm_client_output_path(
                target_dir, contract_name, app_spec_contract_name
            )

            if not generated_file.exists():
                raise FileNotFoundError(
                    f"Expected generated AVM client '{generated_file.name}' was not created by puyapy-clientgen"
                )

            if desired_file.exists():
                desired_file.unlink()

            generated_file.rename(desired_file)
            logger.info(f"Renamed AVM client to {desired_file.name}")
    canonical_app_spec_path = _sync_src_artifacts(output_dir, contract_name)
    if client_file:
        return canonical_app_spec_path or output_dir / client_file
    return output_dir


# --------------------------- Main Logic --------------------------- #


def main(action: str, contract_name: str | None = None) -> None:
    """Main entry point to build and/or deploy smart contracts."""
    artifact_path = root_path / "artifacts"
    # Filter contracts based on an optional specific contract name.
    filtered_contracts = [
        contract
        for contract in contracts
        if contract_name is None or contract.name == contract_name
    ]

    match action:
        case "build":
            for contract in filtered_contracts:
                logger.info(f"Building app at {contract.path}")
                build(artifact_path / contract.name, contract.name, contract.path)
        case "deploy":
            for contract in filtered_contracts:
                output_dir = artifact_path / contract.name
                app_spec_path = _get_app_spec_path(output_dir, contract.name)
                if app_spec_path is None:
                    raise Exception("Could not deploy app, .arc56.json file not found")
                if contract.deploy:
                    logger.info(f"Deploying app {contract.name}")
                    contract.deploy()
        case "all":
            for contract in filtered_contracts:
                logger.info(f"Building app at {contract.path}")
                build(artifact_path / contract.name, contract.name, contract.path)
                if contract.deploy:
                    logger.info(f"Deploying {contract.name}")
                    contract.deploy()
        case _:
            logger.error(f"Unknown action: {action}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main("all")
