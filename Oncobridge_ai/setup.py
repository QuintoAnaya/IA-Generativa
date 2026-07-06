from setuptools import setup, find_packages

setup(
    name="oncobridge-ai",
    version="1.0.0",
    description="Sistema de apoyo al diagnostico oncologico (CDSS) - Trabajo Final IA Generativa para Biomedicina",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "google-generativeai>=0.7.0",
        "python-dotenv>=1.0.0",
    ],
)
