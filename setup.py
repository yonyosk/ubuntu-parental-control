from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ubuntu-parental-control",
    version="1.0.0",
    author="Yonatan Kramer",
    author_email="",
    description="A comprehensive parental control system for Ubuntu",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yonyosk/ubuntu-parental-control",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "parental_control": [
            "templates/*.html",
            "static/css/*",
            "static/js/*"
        ],
    },
    install_requires=[
        "Flask>=2.0.0",
        "requests>=2.25.0",
        "python-dateutil>=2.8.0",
        "typing-extensions>=3.7.0",
        "setuptools>=45.0.0",
        "tinydb>=4.7.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "ubuntu-parental-web=parental_control.web_interface:main",
            "ubuntu-parental-cli=parental_control.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Systems Administration",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    keywords="parental control ubuntu web filter dns content filter",
    project_urls={
        "Bug Reports": "https://github.com/yonyosk/ubuntu-parental-control/issues",
        "Source": "https://github.com/yonyosk/ubuntu-parental-control",
    },
)