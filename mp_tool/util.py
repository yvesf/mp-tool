import argparse
import platform


class UsageAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        formatter = parser._get_formatter()
        formatter.add_usage(parser.usage,
                            parser._actions,
                            parser._mutually_exclusive_groups)

        formatter.start_section(parser._optionals.title)
        formatter.end_section()
        print(formatter.format_help())
        parser.exit(0)


class HelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        formatter = parser._get_formatter()
        formatter.add_usage(parser.usage,
                            parser._actions,
                            parser._mutually_exclusive_groups)

        formatter.start_section(parser._optionals.title)
        formatter.add_text(parser._optionals.description)
        formatter.add_arguments(parser._optionals._group_actions)
        formatter.end_section()

        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]

        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            subparsers = subparsers_action.choices
            for subaction in subparsers_action._get_subactions():
                subparser = subparsers[subaction.dest]
                usage = formatter._format_actions_usage(subparser._actions, [])
                formatter.start_section("{} {}".format(subaction.dest, usage))
                formatter.add_text(subaction.help)
                formatter.add_arguments(subparser._positionals._group_actions)
                formatter.add_arguments(filter(lambda a: not isinstance(a, argparse._HelpAction),
                                               subparser._optionals._group_actions))
                formatter.end_section()

        print(formatter.format_help())
        parser.exit(0)


def format_subcommands_help(parser: argparse.ArgumentParser):
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)]

    formatter = parser._get_formatter()
    formatter.add_usage(parser.usage,
                        parser._actions,
                        parser._mutually_exclusive_groups)

    formatter.start_section("Choose subcommand")
    for subparsers_action in subparsers_actions:
        formatter.add_argument(subparsers_action)
    formatter.end_section()

    return formatter.format_help()


def get_default_serial_port() -> str:
    if platform.system() == "Windows":
        return 'COM3'
    else:
        return '/dev/ttyUSB0'
