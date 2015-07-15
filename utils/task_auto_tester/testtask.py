#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
import difflib
import getopt
import glob
import os
import sys
import time

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))),'..','..'))

import common.courses
import common.tasks
from common.base import load_json_or_yaml
from backend.job_managers.local import LocalJobManager
from backend.job_managers.remote_docker import RemoteDockerJobManager
from backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
from common.course_factory import create_factories
from frontend.common.parsable_text import ParsableText

def job_done_callback(result, i, filename, inputfiles, data):
    print '\x1b[34;1m[' + str(i) + '/' + str(len(inputfiles)) + ']' + " Testing input file : " + filename + '\033[0m'

    job = _parse_text(task, result)

    # Print stdout if verbose
    if verbose:
        print '\x1b[1m-> Complete standard output : \033[0m'
        for line in result['stdout'].splitlines(1):
            print '\t' + line.strip('\n')

    # Start the comparison
    noprob = True

    if 'stderr' in result and result['stderr']:
        noprob = False
        print '\x1b[31;1m-> There was some error(s) during execution : \033[0m'
        for line in result['stderr'].splitlines(1):
            print '\x1b[31;1m\t' + line.strip('\n') + '\033[0m'

    if 'stdout' in data and data['stdout']:
        if data['stdout'] != result['stdout']:
            noprob = False
            print "\033[1m-> Standard output doesn't match :\033[0m"
            for line in difflib.unified_diff(data['stdout'].splitlines(1), result['stdout'].splitlines(1), fromfile='Expected', tofile='Actual'):
                print '\t' + line.strip('\n')

    if 'result' in data and data['result']:
        if data['result'] != result['result']:
            noprob = False
            print "\033[1m-> Result doesn't match :\033[0m"
            print "\t Expected result : " + data['result']
            print "\t Actual result : " + result['result']

    if 'text' in data and data['text']:
        if not 'text' in result:
            noprob = False
            print "\033[1m-> No global feedback given \033[0m"
            print "\t Expected result : " + data['text']
        elif data['text'].strip() != result['text'].strip():
            noprob = False
            print "\033[1m-> Global feedback doesn't match :\033[0m"
            print "\t Expected result : " + data['text']
            print "\t Actual result : " + result['text']

    if 'problems' in data and data['problems']:
        if not 'problems' in result:
            noprob = False
            print "\033[1m-> No specific problem feedback given as expected \033[0m"
        else:
            for problem in data['problems']:
                if not problem in result['problems']:
                    noprob = False
                    print "\033[1m-> No feedback for problem id " + problem + " given \033[0m"
                    print "\t Expected result : " + data['problems'][problem]
                elif data['problems'][problem].strip() != result['problems'][problem].strip():
                    noprob = False
                    print "\033[1m-> Feedback for problem id " + problem + " doesn't match :\033[0m"
                    print "\t Expected result : " + data['problems'][problem]
                    print "\t Actual result : " + result['problems'][problem]

    if 'tests' in data and data['tests']:
        if not 'tests' in result:
            noprob = False
            print "\033[1m-> No tests results given as expected \033[0m"
        else:
            for tag in data['tests']:
                if not tag in result['tests']:
                    noprob = False
                    print "\033[1m-> No test result with tag '" + tag + "' given \033[0m"
                    print "\t Expected result : " + data['tests'][tag]
                elif data['tests'][tag] != result['tests'][tag]:
                    noprob = False
                    print "\033[1m-> Test with tag '" + tag + "' failed :\033[0m"
                    print "\t Expected result : " + data['tests'][tag]
                    print "\t Actual result : " + result['tests'][tag]

    if noprob:
        print "\033[32;1m-> All tests passed \033[0m"

def get_job_manager(config):
    if backend_type == "local":
        return LocalJobManager(config.get('containers', {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
                                      task_directory,
                                      course_factory,
                                      task_factory,
                                      config.get('local_agent_tmp_dir', "/tmp/inginious_agent"))
    elif backend_type == "remote":
        return RemoteDockerJobManager(config.get("docker_daemons", []),
                                             config.get('containers',
                                                        {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
                                             task_directory,
                                             course_factory,
                                             task_factory)
    elif backend_type == "remote_manual":
        return RemoteManualAgentJobManager(
            config.get("agents", [{"host": "localhost", "port": 5001}]),
            config.get('containers', {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
            task_directory,
            course_factory,
            task_factory)
    else:
        raise Exception("Unknown backend {}".format(backend_type))

def get_config():
    if os.path.isfile("./configuration.yaml"):
        configfile = "./configuration.yaml"
    elif os.path.isfile("./configuration.json"):
        configfile = "./configuration.json"
    else:
        raise Exception("No configuration file found")

    return load_json_or_yaml(configfile)

def launch_job(i, filename, data, inputfiles):
    job_manager.new_job(task, data["input"],
                        (lambda job: job_done_callback(job, i, filename, inputfiles, data)),
                        "Task tester",
                        True)

def usage():
    print "Usage : test_task [-v|--verbose]  course_id/task_id"
    print "Verbose mode prints the entire standard output from the task"
    sys.exit(1)

def _parse_text(task, job_result):
    if "text" in job_result:
        job_result["text"] = ParsableText(job_result["text"], task.get_response_type()).parse()
    if "problems" in job_result:
        for problem in job_result["problems"]:
            job_result["problems"][problem] = ParsableText(job_result["problems"][problem], task.get_response_type()).parse()
    return job_result

if __name__ == "__main__":

    # We need to be sudo to run docker
    if not os.name == 'nt':
        euid = os.geteuid()
        if euid != 0:
            print "Script not started as root. Exiting..."
            exit(2)

    # Read arguments from the command line
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'v', ['verbose'])
        if not args:
            usage()
    except getopt.GetoptError as e:
        print e
        sys.exit(1)

    verbose = False
    for opt, arg in opts:
        if opt in ('-v', '--verbose'):
            verbose = True

    # Read input argument
    ids = args[0].split('/')
    courseid = ids[0]
    taskid = ids[1]

    # Load configuration
    config = get_config()

    # Initialize course/task factory and job manager
    task_directory = config["tasks_directory"]
    backend_type = config.get("backend", "local")
    course_factory, task_factory = create_factories(task_directory)
    job_manager = get_job_manager(config)
    job_manager.start()

    # Open the taskfile
    task = course_factory.get_course(courseid).get_task(taskid)
    limits = task.get_limits()

    # List inputfiles
    inputfiles = glob.glob(task_directory + "/" + courseid + "/" + taskid + '/*.test')

    # Ensure job manager is entirely loaded
    # TODO : Hook (for all types of job managers...)
    time.sleep(3)

    for i, filename in enumerate(inputfiles):
        filename = os.path.basename(filename)

        # Open the input file and merge with limits
        try:
            inputfile = open(task_directory + "/" + courseid + "/" + taskid + '/' + filename, 'r')
        except IOError as e:
            print e
            exit(2)

        data = common.custom_yaml.load(inputfile)
        data['limits'] = limits

        launch_job(i+1, filename, data, inputfiles)


# TODO : Kill script at the end of process