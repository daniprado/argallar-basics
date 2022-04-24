from setuptools import setup

setup(
    name='argallar-basics',
    version='0.1.0-c',
    py_modules=[
      'dotfiler',
      'nvim_broadcast',
    ],
    install_requires=[
        'Click',
        'pynvim',
    ],
    entry_points={
        'console_scripts': [
            'ag-linker = dotfiler:linker',
            'ag-dotfiler = dotfiler:dotfiler',
            'ag-nvim-broadcast = nvim_broadcast:cli',
        ],
    },
)
