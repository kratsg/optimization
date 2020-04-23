from setuptools import setup, find_packages
import os, io

extras_require = {
    "plot": ["rootpy"],
    "develop": ["pytest", "pytest-runner", "flake8", "black", "bumpversion"],
}
extras_require["complete"] = sorted(set(sum(extras_require.values(), [])))


def read(*filenames, **kwargs):
    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("sep", "\n")
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


long_description = read(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.rst")
)

setup(
    name="root_optimize",
    version="0.8.4",
    python_requires=">=3",
    description="Perform optimizations on flat ROOT TTrees",
    author="Giordon Stark",
    author_email="kratsg@gmail.com",
    url="https://github.com/kratsg/optimization",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=["tests"]),
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Development Status :: 4 - Beta",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering",
        "Topic :: Utilities",
    ],
    install_requires=["joblib", "numexpr", "tqdm", "formulate", "uproot"],
    extras_require=extras_require,
    entry_points={
        "console_scripts": ["rooptimize=root_optimize.commandline:rooptimize"]
    },
)
