"""Command line subcommand for installing a mlonmcu environment."""
import mlonmcu.setup.tasks
import mlonmcu.context
from mlonmcu.setup import setup

from mlonmcu.cli.common import (
    add_common_options,
    add_context_options,
    handle_logging_flags,
)
from .helper.parse import extract_config_and_init_features


def get_parser(subparsers):
    """ "Define and return a subparser for the setup subcommand."""
    parser = subparsers.add_parser("setup", description="Setup ML on MCU dependencies.")
    parser.set_defaults(func=handle)
    add_common_options(parser)
    add_context_options(parser)
    parser.add_argument(
        "-f",
        "--feature",
        type=str,
        metavar="FEATURE",
        # nargs=1,
        action="append",
        choices=[],  # FIXME: only setup features?
        help="Enabled features for setup (choices: %(choices)s)",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="KEY=VALUE",
        nargs="+",
        action="append",
        help="Set a number of key-value pairs "
        "(do not put spaces before or after the = sign). "
        "If a value contains spaces, you should define "
        "it with double quotes: "
        'foo="this is a sentence". Note that '
        "values are always treated as strings.",
    )
    parser.add_argument(
        "-p",
        "--progress",
        action="store_true",
        help="Display progress bar (default: %(default)s)",
    )
    parser.add_argument(
        "-r",
        "--rebuild",
        action="store_true",
        help="Trigger a rebuild/refresh of already installed dependencies (default: %(default)s)",
    )
    return parser


def handle(args):
    with mlonmcu.context.MlonMcuContext(path=args.home, lock=True) as context:
        config, features = extract_config_and_init_features(args)
        installer = setup.Setup(features=features, config=config, context=context)
        installer.install_dependencies(
            progress=args.progress,
            rebuild=args.rebuild,
        )
