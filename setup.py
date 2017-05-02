from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    "aiohttp>=2.0.0",
    "voluptuous>=0.9.3",
]

setup(
    name='aioautomatic',
    version='0.3.1',
    description="Asyncio library for the Automatic API",
    long_description=readme,
    author="Adam Mills",
    author_email='adam@armills.info',
    url='https://github.com/armills/aioautomatic',
    packages=[
        'aioautomatic',
    ],
    package_dir={'aioautomatic':
                 'aioautomatic'},
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='aioautomatic',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
