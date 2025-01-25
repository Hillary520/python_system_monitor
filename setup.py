from setuptools import setup, find_packages

setup(
    name="python_system_monitor",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "psutil>=5.8.0",
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-asyncio>=0.14.0',
            'pytest-mock>=3.5.0',
            'pytest-cov>=2.12.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'system-monitor=python_system_monitor.main:run',
        ],
    },
    python_requires=">=3.7",
)
