#!/usr/bin/env python3
"""
This script is to convert PK-timezone to UTC
"""

__author__ = "Your Name"
__version__ = "0.1.0"
__license__ = "MIT"

import os
import json
import sys
import argparse
from datetime import datetime, timedelta, timezone
from logzero import logger, logfile


class FunctionFailed(Exception):
    """We use this custome exception whenever our function fails for any reason
    The caller will not receive any other exception"""


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def convert_string_date_to_utc(date):
    """This function converts string datetime to utc datetime"""
    try:
        # Create PK timezone
        pk_delta = timedelta(hours=5)
        pk_timezone = timezone(pk_delta)
        # Create UTC timezone
        utc_delta = timedelta(hours=0)
        utc_timezone = timezone(utc_delta)
        # Date object without timzeone information
        dt_obj = datetime.strptime(date, DATE_FORMAT)
        # Convert date object into Pk timezone object
        pk_obj = dt_obj.replace(tzinfo=pk_timezone)
        # convert date objet in UTC
        utc_obj = pk_obj.astimezone(tz=utc_timezone)
        return utc_obj.strftime(DATE_FORMAT)
    except Exception as exep:
        logger.error("%s", exep)
        raise FunctionFailed from Exception


def create_log():
    """it creates log file, default file name is current timestamp
    "log-20210928220001.log" year month date hour minute seconds"""
    if not os.path.isdir("logs"):
        os.mkdir("logs")
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d%H%M%S")
        logfile(os.path.join("logs", f"log-{dt_string}.log"))
        logger.info("Logs folder created")
    else:
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d%H%M%S")
        logfile(os.path.join("logs", f"log-{dt_string}.log"))


def validate_path_folder(path):
    """this function validates user given folder path,
    incase valid path returns the path"""
    if os.path.isdir(path):
        validated_path = path
    else:
        logger.error("Path is not a folder")
        raise FunctionFailed from Exception

    return validated_path


def is_exist_json(folderpath):
    """it checks either 'json' file exists or not"""
    filepath = f"{os.path.join(folderpath, 'result.json')}"
    if os.path.isfile(filepath):
        json_existed = filepath
    else:
        logger.error("<%s> does not contain 'result.json' file", folderpath)
        raise FunctionFailed from Exception

    return json_existed


def read_json(filepath):
    """it reads json data, if valid json returns
    the data otherwise exit the program"""
    with open(filepath, "r", encoding="utf-8") as file:
        try:
            json_file = json.load(file)
        except json.decoder.JSONDecodeError as err:
            logger.error("Invalid JSON provided <%s>", err)
            raise FunctionFailed from Exception
        return json_file


def split_json_weekly_basis(json_data):
    """This function splits json into weekly basis"""
    output_file_name = 1
    initial_post_date = datetime.strptime(
        json_data["messages"][0]["date"], DATE_FORMAT
    ).date()
    after_week = initial_post_date + timedelta(days=6)

    content = {
        "name": json_data["name"],
        "type": json_data["type"],
        "id": json_data["id"],
        "messages": [],
    }

    for message in json_data["messages"]:
        date = datetime.strptime(message["date"], DATE_FORMAT).date()
        if date <= after_week:
            content["messages"].append(message)
        elif date > after_week:
            generate_json(content, f"tests\\week-{output_file_name}.json")
            output_file_name += 1
            content["messages"] = []
            content["messages"].append(message)
            after_week = date + timedelta(days=6)

        if message == json_data["messages"][-1]:
            generate_json(content, f"tests\\week-{output_file_name}.json")


def generate_json(content, output_file_name):
    """This function generates the json file"""
    with open(output_file_name, "w", encoding="utf-8") as file:
        json.dump(content, file, indent=2)


def main():
    """ Main entry point of the app """
    try:
        create_log()
        parser = argparse.ArgumentParser()
        # Required positional argument
        parser.add_argument("arg", help="Use for source file path, this is required.")
        # for sorting order, 'asc' for ascending, 'desc' for descending. by default sorted by 'desc'
        parser.add_argument(
            "-s",
            dest="sort",
            default="desc",
            help="""To sord post, use 'asc' for ascending,
                    'desc' for descending order. by default sorted by 'desc'""",
        )
        if len(sys.argv) == 1:
            logger.error("Source file was not provided.")
            parser.print_help()
            raise FunctionFailed from Exception
        args = parser.parse_args()
        # path from cmd
        path = args.arg
        # folder path after validation
        folderpath = validate_path_folder(path)
        # json file path
        json_path = is_exist_json(folderpath)
        # json data
        json_data = read_json(json_path)
        # split json file
        split_json_weekly_basis(json_data)

        sys.exit(0)
    except FunctionFailed:
        logger.error("Program terminated unspectedly")
        sys.exit(1)


if __name__ == "__main__":
    main()
