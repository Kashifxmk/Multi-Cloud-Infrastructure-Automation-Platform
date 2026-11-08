import os
from typing import Any

from .base import CapabilityResult, VerificationResult


class AwsStsAdapter:
    provider = "aws"
    simulated = False

    def verify(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> VerificationResult:
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError as error:
            raise RuntimeError("AWS verification requires the boto3 package") from error

        config = auth_config or {}
        session_kwargs: dict[str, Any] = {}
        profile = config.get("profile") or os.getenv("AWS_PROFILE")
        region = config.get("region") or os.getenv("AWS_REGION") or "us-east-1"
        role_arn = config.get("role_arn")
        if profile:
            session_kwargs["profile_name"] = profile
        session = boto3.Session(region_name=region, **session_kwargs)
        client = session.client("sts")
        try:
            assume_role = None
            if role_arn:
                assume_role_kwargs = {
                    "RoleArn": role_arn,
                    "RoleSessionName": "cloudpilot-read-only-verification",
                }
                if config.get("external_id"):
                    assume_role_kwargs["ExternalId"] = config["external_id"]
                assume_role = client.assume_role(**assume_role_kwargs)
            if assume_role:
                credentials = assume_role["Credentials"]
                client = boto3.client(
                    "sts",
                    region_name=region,
                    aws_access_key_id=credentials["AccessKeyId"],
                    aws_secret_access_key=credentials["SecretAccessKey"],
                    aws_session_token=credentials["SessionToken"],
                )
            identity = client.get_caller_identity()
        except (BotoCoreError, ClientError) as error:
            raise RuntimeError("AWS read-only identity verification failed") from error

        account_id = str(identity.get("Account", "")).strip()
        if account_identifier and account_identifier != account_id:
            raise RuntimeError("AWS account identity does not match the configured account")
        return VerificationResult(
            provider=self.provider,
            identity=account_id,
            regions=(region,),
            capabilities=("identity",),
            simulated=False,
        )

    def capabilities(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> CapabilityResult:
        config = auth_config or {}
        region = config.get("region") or os.getenv("AWS_REGION") or "us-east-1"
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError as error:
            raise RuntimeError("AWS capability discovery requires the boto3 package") from error
        try:
            session = boto3.Session(
                region_name=region,
                profile_name=config.get("profile") or os.getenv("AWS_PROFILE"),
            )
            regions = tuple(
                item["RegionName"]
                for item in session.client("ec2", region_name=region).describe_regions()["Regions"]
            )
        except (BotoCoreError, ClientError) as error:
            raise RuntimeError("AWS capability discovery failed") from error
        return CapabilityResult(
            provider=self.provider,
            regions=regions or (region,),
            resource_types=("network", "compute", "storage", "database"),
            machine_types=("t3.micro", "t3.medium", "m6i.large"),
            permissions=("sts:GetCallerIdentity", "ec2:DescribeRegions", "ec2:DescribeInstanceTypes"),
            simulated=False,
        )
