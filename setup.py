from setuptools import setup

setup(
    name="code_backup",
    version="1.0",
    py_modules=["script"], # This must match your file name (script.py)
    entry_points={
        'console_scripts': [
            'code_backup=script:main', # Command=FileName:Function
        ],
    },
)