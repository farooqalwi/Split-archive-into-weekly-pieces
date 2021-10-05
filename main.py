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
import shutil
import argparse
from datetime import datetime, timedelta, timezone
import weakref
from colorama.initialise import init
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


def is_exist_json(rootfolder):
    """it checks either 'json' file exists or not"""
    filepath = f"{os.path.join(rootfolder, 'result.json')}"
    if os.path.isfile(filepath):
        json_existed = filepath
    else:
        logger.error("<%s> does not contain 'result.json' file", rootfolder)
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


def create_output_folder(rootfolder, subfoldername):
    """This function creates output folders with respective dates"""
    if not os.path.isdir(os.path.join(rootfolder, "output")):
        os.mkdir(os.path.join(rootfolder, "output"))
        logger.info("Output folder created")
    
    if os.path.isdir(os.path.join(rootfolder, "output", subfoldername)):
        shutil.rmtree(os.path.join(rootfolder, "output", subfoldername))
        logger.info("old %s subfolder removed", subfoldername)
    os.mkdir(os.path.join(rootfolder, "output", subfoldername))
    logger.info("%s subfolder created", subfoldername)


def move_photo(rootfolder, photo, initial_post_date, after_week):
    """This function moves photo to subfolde as respect to its post date"""
    try:
        shutil.move(os.path.join(rootfolder, photo), os.path.join(rootfolder, "output", f"{initial_post_date} - {after_week}"))
        logger.info("%s moved to subfolder %s - %s", photo, initial_post_date, after_week)
    except FileNotFoundError:
        logger.error("%s not found", photo)


def delete_photo_folder(rootfolder):
    """This function deletes photo folder after all photos move to respected date folders"""
    if os.path.isdir(os.path.join(rootfolder, "photos")):
        shutil.rmtree(os.path.join(rootfolder, "photos"))


def split_json_weekly_basis(rootfolder, json_data):
    """This function splits json into weekly basis"""
    no_of_days = input("Enter no of days to split json: ")
    try:
        no_of_days = int(no_of_days)
    except ValueError:
        logger.error("%s must be an integer", no_of_days)
        raise FunctionFailed from Exception
    output_file_name = 1
    initial_post_date = datetime.strptime(
        json_data["messages"][0]["date"], DATE_FORMAT
    ).date()
    after_week = initial_post_date + timedelta(days=no_of_days - 1)
    create_output_folder(rootfolder, f"{initial_post_date} - {after_week}")

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
            generate_json(rootfolder, content, f"{initial_post_date} - {after_week}")
            logger.info("%s - %s.json created", initial_post_date, after_week)
            output_file_name += 1
            content["messages"] = []
            content["messages"].append(message)
            initial_post_date = date
            after_week += timedelta(days=(no_of_days))
            create_output_folder(rootfolder, f"{initial_post_date} - {after_week}")

        if message == json_data["messages"][-1]:
            generate_json(rootfolder, content, f"{initial_post_date} - {after_week}")
            logger.info("%s - %s.json created", initial_post_date, after_week)
            delete_photo_folder(rootfolder)
        
        if "photo" in message:
            move_photo(rootfolder, message["photo"], initial_post_date, after_week)


def generate_json(rootfolder, content, output_name):
    """This function generates the json file"""
    outputpath = os.path.join(rootfolder, "output", output_name, f"{output_name}.json")
    with open(outputpath, "w", encoding="utf-8") as file:
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
        rootfolder = validate_path_folder(path)
        # json file path
        json_path = is_exist_json(rootfolder)
        # json data
        json_data = read_json(json_path)
        # split json file
        split_json_weekly_basis(rootfolder, json_data)

        sys.exit(0)
    except FunctionFailed:
        logger.error("Program terminated unspectedly")
        sys.exit(1)


if __name__ == "__main__":
    main()
