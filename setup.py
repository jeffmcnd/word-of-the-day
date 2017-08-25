from setuptools import setup

setup(
    name='word_of_the_day',
    packages=['word_of_the_day'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
