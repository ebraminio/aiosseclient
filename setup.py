from setuptools import setup


setup(
    name='aiosseclient',
    version='0.0.1',
    description='Asynchronous Server Sent Event strems client.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Ebrahim Byagowi',
    author_email='ebrahim@gnu.org',
    url='https://github.com/ebraminio/aiosseclient',
    license=open('LICENSE').read(),
    install_requires=['aiohttp'],
    py_modules=['aiosseclient'],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5"
    ]
)

