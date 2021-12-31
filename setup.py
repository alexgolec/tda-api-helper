import setuptools

with open('README.rst', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='tda-api-helper',
    version='0.0.1',
    author='Alex Golec',
    author_email='bottomless.septic.tank@gmail.com',
    description='A Discord bot to notify users of frequently asked questions',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/alexgolec/tda-api-helper',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
    python_requires='>=3.9',
    install_requires=[
        'discord.py',
        'sqlalchemy',
        'pyyaml',
    ],
    extras_require={
        'dev': [
            'asynctest',
            'colorama',
            'coverage',
            'tox',
            'nose',
            'pytest',
        ]
    },
    keywords='finance trading equities bonds options research',
    project_urls={
        'Source': 'https://github.com/alexgolec/tda-api-helper',
        'Tracker': 'https://github.com/alexgolec/tda-api-helper/issues',
    },
    license='MIT',
)

