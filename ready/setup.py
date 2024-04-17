from setuptools import setup, find_packages

setup(
    name='background',  # This should be the name of your package.
    version='0.1.0',
    packages=find_packages(),  # This will find all packages in the directory.
    description='A package for cryptocurrency backtesting.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/your-repo',  # Replace with the URL to your repository.
    install_requires=[
        # Any dependencies you need, e.g., 'numpy', 'pandas'
        'numpy',
        'pandas',
        'talib-binary',  # Just as an example if you use TA-Lib
        # Include any other dependencies you have here
    ],
    python_requires='>=3.6',  # Adjust depending on your Python version requirements
)
