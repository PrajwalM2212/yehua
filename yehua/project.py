import os
import yaml

from datetime import datetime
from jinja2 import Environment, FileSystemLoader

import yehua.utils as utils


class Project:
    def __init__(self, yehua_file):
        if not os.path.exists(yehua_file):
            raise Exception("%s does not exist" % yehua_file)
        self.project_file = yehua_file
        self.project_name = None
        self.answers = None
        self.name = None
        self.directives = None
        self._ask_questions()
        self._append_magic_variables()
        self._template_yehua_file()

    def create_all_directories(self):
        folder_tree = {
            self.answers['project_name']: self.directives.get('layout', None)
        }
        utils.make_directories(None, folder_tree)

    def get_mobans(self):
        for repo in self.directives['mobans']:
            for key, value in repo.items():
                cmd = 'cd %s && git clone %s %s' % (
                    self.answers['project_name'],
                    value, key)
                os.system(cmd)

    def templating(self):
        for template in self.directives['templates']:
            for output, template_file in template.items():
                template = self.jj2_environment.get_template(template_file)
                rendered_content = template.render(**self.answers)
                target = os.path.join(self.project_name, output)
                utils.save_file(target, rendered_content)

    def copy_static_files(self):
        for static in self.directives['static']:
            for output, source in static.items():
                source = os.path.abspath(os.path.join(self.static_dir, source))
                dest = os.path.join(self.project_name, output)
                utils.copy_file(source, dest)

    def inflate_all_by_moban(self):
        cmd = 'cd %s && moban' % self.answers['project_name']
        os.system(cmd)

    def initialize_git_and_add_all(self):
        project_name = self.answers['project_name']
        cmd = 'cd %s && git init' % project_name
        project_files = [
            "CHANGELOG.rst",
            "MANIFEST.in",
            "Makefile",
            "README.rst",
            "%s.yml" % project_name,
            "%s" % utils.make_project_src(project_name),
            "docs",
            "requirements.txt",
            "setup.cfg",
            "setup.py",
            "test.sh",
            "tests",
            ".gitignore",
            ".moban.d",
            ".travis.yml",
            ".moban.yml"
        ]
        for file in project_files:
            cmd = 'cd %s && git add' % project_name
            os.system(cmd)
        print("Please review changes before commit!")

    def _ask_questions(self):
        base_path = os.path.dirname(self.project_file)
        with open(self.project_file, "r") as f:
            first_stage = yaml.load(f)
            print(first_stage['introduction'])
            self.template_dir = os.path.join(
                base_path,
                first_stage['configuration']['template_path'])
            self.static_dir = os.path.join(
                base_path,
                first_stage['configuration']['static_path'])
            self.answers = get_user_inputs(first_stage['questions'])

    def _append_magic_variables(self):
        self.project_name = self.answers['project_name']
        self.answers['now'] = datetime.utcnow()

        self.jj2_environment = self._create_jj2_environment(self.template_dir)

    def _template_yehua_file(self):
        base_path = os.path.dirname(self.project_file)
        tmp_env = self._create_jj2_environment(base_path)
        template = tmp_env.get_template(os.path.basename(self.project_file))
        renderred_content = template.render(
            **self.answers
        )
        self.directives = yaml.load(renderred_content)

    def _create_jj2_environment(self, path):
        template_loader = FileSystemLoader(path)
        environment = Environment(
            loader=template_loader,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True)
        return environment


def get_user_inputs(questions):
    answers = {}
    for q in questions:
        for key, question in q.items():
            if isinstance(question, list):
                q, additional = raise_complex_question(question)
                answers[key] = q
                if additional:
                    answers.update(additional)
            else:
                a = utils.yehua_input(question + ' ')
                answers[key] = a
    return answers


def raise_complex_question(question):
    additional_answers = None
    for subq in question:
        subquestion = subq.pop('question')
        suggested_answers = sorted(subq.keys())
        long_question = [subquestion] + suggested_answers
        choice = '(%s): ' % (
            ','.join([str(x) for x in range(1, len(long_question))]))
        long_question.append(choice)
        a = utils.yehua_input('\n'.join(long_question))
        for key in suggested_answers:
            if key.startswith(a) and subq[key] != 'N/A':
                additional_answers = get_user_inputs(subq[key])
        break
    return a, additional_answers
