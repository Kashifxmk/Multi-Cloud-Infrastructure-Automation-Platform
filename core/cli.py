import argparse
import logging
from pathlib import Path

from .config_loader import load_config
from .config_validator import require_valid_config
from .provider_manager import terraform_directory
from .report_generator import write_report
from .terraform_manager import TerraformManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CloudPilot multi-cloud automation CLI")
    parser.add_argument("command", choices=["validate", "plan", "deploy", "status", "destroy"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--yes", action="store_true", help="Confirm destructive operations")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        config = load_config(args.config)
        require_valid_config(config)
        if args.command == "validate":
            print("Configuration is valid.")
            return 0
        if args.command == "destroy" and not args.yes:
            raise ValueError("Destroy requires explicit confirmation with --yes")
        manager = TerraformManager(terraform_directory(config["cloud"]["provider"], Path.cwd()))
        manager.init()
        variables = {"region": str(config["cloud"]["region"])}
        if args.command == "plan":
            manager.plan(variables)
            print("Terraform plan completed.")
        elif args.command == "deploy":
            manager.plan(variables)
            manager.apply(variables)
            write_report(config, "deployed", manager.outputs())
            print("Deployment completed.")
        elif args.command == "status":
            outputs = manager.outputs()
            write_report(config, "available", outputs)
            print(outputs)
        elif args.command == "destroy":
            manager.destroy(variables)
            write_report(config, "destroyed")
            print("Destroy completed.")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        logging.error("%s", error)
        return 1
