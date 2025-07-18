#!/usr/bin/env python3
"""
Setup configuration for AI Calendar Assistant
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        return f.read()

# Read requirements from requirements.txt
def read_requirements(filename):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename), encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ai-calendar-assistant",
    version="1.2.0",
    description="Azure OpenAI powered calendar assistant with Microsoft Graph integration and multi-agent orchestration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="drewelewis",
    author_email="drew@example.com",
    url="https://github.com/drewelewis/ai-calendar-assistant",
    project_urls={
        "Bug Tracker": "https://github.com/drewelewis/ai-calendar-assistant/issues",
        "Documentation": "https://github.com/drewelewis/ai-calendar-assistant/wiki",
        "Source Code": "https://github.com/drewelewis/ai-calendar-assistant",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Communications :: Chat",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': read_requirements('requirements-dev.txt'),
        'test': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'httpx>=0.25.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'ai-calendar=main:main',
            'ai-calendar-cli=multi_agent_cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.yaml', '*.yml', '*.json', '*.md', '*.txt'],
    },
    zip_safe=False,
    keywords=[
        'azure', 'openai', 'calendar', 'microsoft-graph', 
        'ai-assistant', 'multi-agent', 'scheduling'
    ],
    license="MIT",
)
