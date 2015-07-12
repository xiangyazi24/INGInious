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
import os
import tempfile
import shutil

import common.base
import common.courses
from common.course_factory import create_factories

class TestCourse(object):
    def setUp(self):
        common.base.init_common_lib(os.path.join(os.path.dirname(__file__), 'tasks'),
                                    [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"],
                                    1024 * 1024)
        self.course_factory, _ = create_factories(os.path.join(os.path.dirname(__file__), 'tasks'))

    def test_course_loading(self):
        '''Tests if a course file loads correctly'''
        print "\033[1m-> common-courses: course loading\033[0m"
        c = self.course_factory.get_course('test')
        assert c.get_id() == 'test'
        assert c._content['accessible'] == True
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 1'

        c = self.course_factory.get_course('test2')
        assert c.get_id() == 'test2'
        assert c._content['accessible'] == '1970-01-01/2033-01-01'
        assert c._content['admins'] == ['testadmin1']
        assert c._content['name'] == 'Unit test 2'

        # This one is in JSON
        c = self.course_factory.get_course('test3')
        assert c.get_id() == 'test3'
        assert c._content['accessible'] == '1970-01-01/1970-12-31'
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 3'

    def test_invalid_coursename(self):
        try:
            self.course_factory.get_course('invalid/name')
        except:
            return
        assert False

    def test_unreadable_course(self):
        try:
            self.course_factory.get_course('invalid_course')
        except:
            return
        assert False

    def test_all_courses_loading(self):
        '''Tests if all courses are loaded by Course.get_all_courses()'''
        print "\033[1m-> common-courses: all courses loading\033[0m"
        c = self.course_factory.get_all_courses()
        assert 'test' in c
        assert 'test2' in c
        assert 'test3' in c

    def test_tasks_loading(self):
        '''Tests loading tasks from the get_tasks method'''
        print "\033[1m-> common-courses: course tasks loading\033[0m"
        c = self.course_factory.get_course('test')
        t = c.get_tasks()
        assert 'task1' in t
        assert 'task2' in t
        assert 'task3' in t
        assert 'task4' in t

    def test_tasks_loading_invalid(self):
        c = self.course_factory.get_course('test3')
        t = c.get_tasks()
        assert t == {}


class TestCourseWrite(object):
    """ Test the course update function """

    def setUp(self):
        self.dir_path = tempfile.mkdtemp()
        common.base.init_common_lib(self.dir_path,
                                    [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"],
                                    1024 * 1024)
        self.course_factory, _ = create_factories(self.dir_path)

    def tearDown(self):
        shutil.rmtree(self.dir_path)
        common.base.init_common_lib(os.path.join(os.path.dirname(__file__), 'tasks'),
                                    [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"],
                                    1024 * 1024)

    def test_course_update(self):
        os.mkdir(os.path.join(self.dir_path, "test"))
        open(os.path.join(self.dir_path, "test", "course.yaml"), "w").write("""
name: "a"
admins: ["a"]
accessible: "1970-01-01/2033-01-01"
        """)
        assert self.course_factory.get_course_descriptor_content("test") == {"name": "a", "admins": ["a"], "accessible": "1970-01-01/2033-01-01"}
        self.course_factory.update_course_descriptor_content("test", {"name": "b", "admins": ["b"], "accessible": "1970-01-01/2030-01-01"})
        assert self.course_factory.get_course_descriptor_content("test") == {"name": "b", "admins": ["b"], "accessible": "1970-01-01/2030-01-01"}
