from aiohttp.web import Application, run_app
import asyncio

from routes import create_routes
import database
import settings

import sys
import os


USER_COMMANDS = list(file.split('.')[0] for file in os.listdir('commands') if file.endswith('.py'))
BASE_COMMANDS = {
    'run_server': run_app
}


def command_handler(loop: asyncio.AbstractEventLoop):
    raw_command = sys.argv[1:]

    if not raw_command:
        raw_command = command_chooser()

    command = raw_command[0]
    args = raw_command[1:]

    if command[0] in USER_COMMANDS:
        # init_database()
        start_user_command(loop, command, args)

    else:
        pass
    # application = init_base()
    # if command[0] in BASE_COMMANDS.keys():
    #     BASE_COMMANDS[command[0]](application)
    # if commands[0] == 'runserver':
    #     run_app(application)
    # elif commands[0] in :


def command_chooser():
    for command_path, path_label in zip([BASE_COMMANDS, USER_COMMANDS], ['Base commands:', 'User commands:']):
        print(path_label)
        for command_to_print in command_path:
            print(f'    {command_to_print}')
        print()

    command = input('Enter command: ').split(' ')
    allowed_commands = list(BASE_COMMANDS.keys()) + USER_COMMANDS
    while command[0] not in allowed_commands:
        command = input('Enter command: ').split(' ')

    return command


def start_user_command(loop: asyncio.AbstractEventLoop, command: str, args: list):
    eval(f'from commands.{command} import handle')

    func = None
    exec(f'func = commands.{command}.handle')
    task = asyncio.tasks.create_task(func(args))
    loop.run_until_complete(task)


def init_base() -> Application:
    application = Application()
    create_routes(application.router)

    return application


if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    command_handler(event_loop)
