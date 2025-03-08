"""Asynchronous Server Side Events (SSE) Client"""
from setuptools import setup

with open('README.md', 'r', encoding='utf8') as f:
    readme = f.read()
with open('LICENSE', 'r', encoding='utf8') as f:
    license_txt = f.read()

setup(
    name='aiosseclient',
    version='0.1.8',
    description='Asynchronous Server Sent Event streams client.',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Ebrahim Byagowi',
    author_email='ebrahim@gnu.org',
    url='https://github.com/ebraminio/aiosseclient',
    license=license_txt,
    install_requires=['aiohttp'],
    py_modules=['aiosseclient'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9'
    ]
)
