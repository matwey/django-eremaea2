import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
	README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
	name='django-eremaea2',
	version='2.0.18',
	packages=['eremaea','eremaea.ctl','eremaea.migrations'],
	entry_points={'console_scripts': [
		'eremaeactl = eremaea.ctl.commandline:execute_from_commandline',
	]},
	include_package_data=True,
	license='BSD-2-Clause',
	description='A simple Django application to store and show webcam snapshots',
	long_description=README,
	long_description_content_type="text/markdown",
	url='https://github.com/matwey/django-eremaea2',
	author='Matwey V. Kornilov',
	author_email='matwey.kornilov@gmail.com',
	classifiers=[
		'Environment :: Web Environment',
		'Framework :: Django',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: BSD License',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 3',
		'Topic :: Internet :: WWW/HTTP',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
	],
	test_suite='runtests.runtests',
	install_requires=[
		'Django',
		'djangorestframework',
		'requests',
		'requests_toolbelt',
		'cmdln',
		'python-magic',
	]
)
