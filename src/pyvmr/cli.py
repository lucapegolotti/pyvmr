"""Command-line interface for pyvmr."""

try:
    import click
except ImportError:
    raise ImportError(
        "CLI dependencies not installed. Install with: pip install pyvmr[cli]"
    )

from .client import VMRClient
from .download import format_size


@click.group()
@click.version_option()
@click.option(
    "--cache-dir",
    type=click.Path(),
    default=None,
    help="Cache directory for catalog data",
)
@click.pass_context
def main(ctx, cache_dir):
    """pyvmr - Python client for the Vascular Model Repository.

    Download and explore cardiovascular models from vascularmodel.com
    """
    ctx.ensure_object(dict)
    ctx.obj["client"] = VMRClient(cache_dir=cache_dir)


@main.command()
@click.option("--species", "-s", help="Filter by species (Human, Animal, H, A)")
@click.option("--anatomy", "-a", help="Filter by anatomy (Aorta, Coronary, etc.)")
@click.option("--disease", "-d", help="Filter by disease")
@click.option("--sex", help="Filter by sex (Male, Female)")
@click.option("--age-min", type=float, help="Minimum age")
@click.option("--age-max", type=float, help="Maximum age")
@click.option("--with-simulations", is_flag=True, help="Only models with simulations")
@click.option("--limit", "-n", type=int, default=20, help="Max results to show")
@click.pass_context
def list(ctx, species, anatomy, disease, sex, age_min, age_max, with_simulations, limit):
    """List models in the repository."""
    vmr = ctx.obj["client"]

    models = vmr.search(
        species=species,
        anatomy=anatomy,
        disease=disease,
        sex=sex,
        age_min=age_min,
        age_max=age_max,
        has_simulations=with_simulations if with_simulations else None,
    )

    if not models:
        click.echo("No models found matching criteria.")
        return

    click.echo(f"Found {len(models)} models" + (f" (showing first {limit})" if len(models) > limit else ""))
    click.echo()

    for model in models[:limit]:
        size_str = f" [{format_size(model.file_size)}]" if model.file_size else ""
        sim_str = " [SIM]" if model.has_simulations else ""
        click.echo(f"  {model.name}: {model.anatomy} | {model.disease} | {model.species}{size_str}{sim_str}")


@main.command()
@click.option("--species", "-s", help="Filter by species")
@click.option("--anatomy", "-a", help="Filter by anatomy")
@click.option("--disease", "-d", help="Filter by disease")
@click.option("--with-simulations", is_flag=True, help="Only models with simulations")
@click.pass_context
def search(ctx, species, anatomy, disease, with_simulations):
    """Search for models matching criteria."""
    vmr = ctx.obj["client"]

    models = vmr.search(
        species=species,
        anatomy=anatomy,
        disease=disease,
        has_simulations=with_simulations if with_simulations else None,
    )

    if not models:
        click.echo("No models found.")
        return

    click.echo(f"Found {len(models)} matching models:")
    click.echo()

    for model in models:
        age_str = f", Age {model.age:.1f}" if model.age else ""
        click.echo(f"  {model.name}")
        click.echo(f"    {model.species} | {model.sex}{age_str}")
        click.echo(f"    {model.anatomy} | {model.disease}")
        if model.has_simulations:
            click.echo(f"    Simulations available")
        click.echo()


@main.command()
@click.argument("name")
@click.pass_context
def info(ctx, name):
    """Show detailed information about a model."""
    vmr = ctx.obj["client"]

    model = vmr.get_model(name)
    if not model:
        click.echo(f"Model not found: {name}")
        return

    click.echo(f"Model: {model.name}")
    click.echo()
    click.echo("Demographics:")
    click.echo(f"  Species:   {model.species}")
    click.echo(f"  Sex:       {model.sex}")
    click.echo(f"  Age:       {model.age}")
    click.echo(f"  Ethnicity: {model.ethnicity or '-'}")
    click.echo()
    click.echo("Classification:")
    click.echo(f"  Anatomy:   {model.anatomy}")
    click.echo(f"  Disease:   {model.disease}")
    click.echo(f"  Procedure: {model.procedure or '-'}")
    click.echo()
    click.echo("Available Data:")
    click.echo(f"  Images:        {'Yes' if model.has_images else 'No'}")
    click.echo(f"  Paths:         {'Yes' if model.has_paths else 'No'}")
    click.echo(f"  Segmentations: {'Yes' if model.has_segmentations else 'No'}")
    click.echo(f"  Models:        {'Yes' if model.has_models else 'No'}")
    click.echo(f"  Meshes:        {'Yes' if model.has_meshes else 'No'}")
    click.echo(f"  Simulations:   {'Yes' if model.has_simulations else 'No'}")

    if model.file_size:
        click.echo()
        click.echo(f"Download Size: {format_size(model.file_size)}")

    if model.doi:
        click.echo()
        click.echo(f"DOI: {model.doi}")

    # Show simulations if available
    if model.has_simulations:
        sims = vmr.get_simulations(name)
        if sims:
            click.echo()
            click.echo("Simulation Results:")
            for sim in sims:
                size_str = f" [{format_size(sim.file_size)}]" if sim.file_size else ""
                click.echo(f"  - {sim.short_name or sim.full_filename}: {sim.method} ({sim.fidelity}){size_str}")


@main.command()
@click.argument("names", nargs=-1, required=True)
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@click.option("--extract", "-x", is_flag=True, help="Extract ZIP files after download")
@click.option("--with-simulations", is_flag=True, help="Also download simulations")
@click.option("--with-pdf", is_flag=True, help="Also download PDF documentation")
@click.pass_context
def download(ctx, names, output, extract, with_simulations, with_pdf):
    """Download one or more models.

    Examples:

        pyvmr download 0001_H_AO_SVD

        pyvmr download 0001_H_AO_SVD 0002_H_AO_H --output ./models/

        pyvmr download 0001_H_AO_SVD --extract --with-simulations
    """
    vmr = ctx.obj["client"]

    if len(names) == 1:
        # Single download
        name = names[0]
        model = vmr.get_model(name)
        if not model:
            click.echo(f"Model not found: {name}")
            return

        click.echo(f"Downloading {name}...")
        if model.file_size:
            click.echo(f"Size: {format_size(model.file_size)}")

        vmr.download(
            name,
            output_dir=output,
            extract=extract,
            include_simulations=with_simulations,
            include_pdf=with_pdf,
        )
        click.echo("Done!")
    else:
        # Batch download
        click.echo(f"Downloading {len(names)} models...")
        vmr.download_batch(
            list(names),
            output_dir=output,
            extract=extract,
            include_simulations=with_simulations,
        )
        click.echo("Done!")


@main.command()
@click.argument("model_name")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@click.option("--extract", "-x", is_flag=True, help="Extract ZIP files after download")
@click.pass_context
def download_simulations(ctx, model_name, output, extract):
    """Download simulation results for a model.

    Example:

        pyvmr download-simulations 0001_H_AO_SVD --output ./sims/
    """
    vmr = ctx.obj["client"]

    sims = vmr.get_simulations(model_name)
    if not sims:
        click.echo(f"No simulations found for: {model_name}")
        return

    click.echo(f"Downloading {len(sims)} simulation files for {model_name}...")
    vmr.download_simulations(model_name, output_dir=output, extract=extract)
    click.echo("Done!")


@main.command()
@click.pass_context
def summary(ctx):
    """Show summary statistics for the repository."""
    vmr = ctx.obj["client"]

    stats = vmr.summary()

    click.echo("VMR Summary")
    click.echo("=" * 40)
    click.echo(f"Total Models: {stats['total']}")
    click.echo()

    click.echo("By Species:")
    for species, count in sorted(stats["by_species"].items()):
        click.echo(f"  {species}: {count}")
    click.echo()

    click.echo("By Anatomy (top 10):")
    anatomy_sorted = sorted(stats["by_anatomy"].items(), key=lambda x: -x[1])[:10]
    for anatomy, count in anatomy_sorted:
        click.echo(f"  {anatomy}: {count}")
    click.echo()

    click.echo("Features:")
    click.echo(f"  With Simulations: {stats['with_simulations']}")
    click.echo(f"  With Meshes: {stats['with_meshes']}")
    click.echo(f"  With Segmentations: {stats['with_segmentations']}")

    if stats["age_statistics"]:
        click.echo()
        click.echo("Age Statistics:")
        click.echo(f"  Min: {stats['age_statistics']['min']:.1f} years")
        click.echo(f"  Max: {stats['age_statistics']['max']:.1f} years")
        click.echo(f"  Mean: {stats['age_statistics']['mean']:.1f} years")

    if stats["total_size_bytes"]:
        click.echo()
        click.echo(f"Total Download Size: {format_size(stats['total_size_bytes'])}")


@main.command()
@click.pass_context
def refresh(ctx):
    """Force refresh of cached catalog data."""
    vmr = ctx.obj["client"]
    click.echo("Refreshing catalog data...")
    vmr.refresh_catalog()
    click.echo("Done!")


@main.command("cache-info")
@click.pass_context
def cache_info(ctx):
    """Show cache status information."""
    vmr = ctx.obj["client"]
    info = vmr.cache_info()

    click.echo(f"Cache Directory: {info['cache_dir']}")
    click.echo(f"Cache TTL: {info['cache_ttl_hours']} hours")
    click.echo()

    if info["resources"]:
        click.echo("Cached Resources:")
        for name, data in info["resources"].items():
            status = "valid" if data["valid"] else "expired"
            size = format_size(data["size_bytes"]) if data["size_bytes"] else "0 B"
            click.echo(f"  {name}: {status} ({size})")
    else:
        click.echo("No cached data.")


if __name__ == "__main__":
    main()
