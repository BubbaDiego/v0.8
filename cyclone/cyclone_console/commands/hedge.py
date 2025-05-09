# cyclone_console/commands/hedge.py

import typer
from rich.console import Console
from rich.table import Table
from core.constants import DB_PATH
from data.data_locker import DataLocker
from sonic_labs.hedge_manager import HedgeManager
from cyclone.cyclone_hedge_service import CycloneHedgeService

app = typer.Typer(help="🛡 Hedge detection and management")

console = Console()
dl = DataLocker(str(DB_PATH))
service = CycloneHedgeService(dl)


@app.command("scan")
def scan_hedges():
    """🔍 Scan DB for hedgeable groups"""
    positions = dl.read_positions()
    if not positions:
        console.print("[red]⚠ No positions available for hedge analysis[/red]")
        return

    manager = HedgeManager(positions)
    groups = manager.get_hedges()

    if not groups:
        console.print("[yellow]⚠ No hedge groups found[/yellow]")
        return

    for i, hedge in enumerate(groups, 1):
        console.print(f"\n[bold cyan]HEDGE GROUP {i}[/bold cyan]")
        console.print(f"Long Size: {hedge.total_long_size:.2f} | Short Size: {hedge.total_short_size:.2f}")
        console.print(f"Total Heat: {hedge.total_heat_index:.2f}")
        console.print("Positions:")
        for pos in hedge.positions:
            console.print(f"  • {pos.get('id')} ({pos.get('position_type')})")


@app.command("link")
def link_hedges():
    """🔗 Assign hedge_buddy_id for linked positions"""
    import asyncio
    asyncio.run(service.link_hedges())
    console.print("[green]✅ Hedge links updated[/green]")


@app.command("clear")
def clear_hedges():
    """🧹 Clear hedge assignments from positions"""
    try:
        HedgeManager.clear_hedge_data()
        console.print("[yellow]🧼 Hedge associations cleared from DB[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error clearing hedge data: {e}[/red]")
