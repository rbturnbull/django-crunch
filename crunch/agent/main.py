import typer

app = typer.Typer()


@app.callback()
def callback():
    """
    Awesome Portal Gun
    """
    typer.echo("Loading portal gun")


