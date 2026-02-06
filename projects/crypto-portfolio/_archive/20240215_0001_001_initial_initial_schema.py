"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-02-15

Creates all initial tables for the crypto portfolio analyzer.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Portfolios
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, default='Default Portfolio'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_cost_basis_method', sa.Enum('fifo', 'lifo', 'hifo', 'avg', name='costbasismethod'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Exchange Connections
    op.create_table(
        'exchange_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('portfolio_id', 'exchange', name='uq_portfolio_exchange')
    )
    
    # Holdings
    op.create_table(
        'holdings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=True),
        sa.Column('amount', sa.Numeric(28, 18), nullable=False, default=0),
        sa.Column('cost_basis_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('last_price_usd', sa.Numeric(18, 8), nullable=True),
        sa.Column('last_price_updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('portfolio_id', 'asset', 'exchange', name='uq_holding')
    )
    op.create_index('ix_holdings_asset', 'holdings', ['asset'])
    op.create_index('ix_holdings_exchange', 'holdings', ['exchange'])
    
    # Transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('tx_type', sa.Enum('buy', 'sell', 'deposit', 'withdrawal', 'transfer_in', 'transfer_out', 'stake', 'unstake', 'staking_reward', 'airdrop', 'fee', 'interest', name='transactiontype'), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(28, 18), nullable=False),
        sa.Column('price_usd', sa.Numeric(18, 8), nullable=True),
        sa.Column('value_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('fee', sa.Numeric(18, 8), nullable=True, default=0),
        sa.Column('fee_asset', sa.String(20), nullable=True),
        sa.Column('exchange', sa.String(50), nullable=True),
        sa.Column('order_id', sa.String(100), nullable=True),
        sa.Column('wallet_address', sa.String(100), nullable=True),
        sa.Column('tx_hash', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_asset', 'transactions', ['asset'])
    op.create_index('ix_transactions_type', 'transactions', ['tx_type'])
    op.create_index('ix_transactions_exchange', 'transactions', ['exchange'])
    op.create_index('ix_transactions_timestamp', 'transactions', ['timestamp'])
    op.create_index('ix_transactions_external_id', 'transactions', ['external_id'])
    
    # Tax Lots
    op.create_table(
        'tax_lots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(28, 18), nullable=False),
        sa.Column('remaining_amount', sa.Numeric(28, 18), nullable=False),
        sa.Column('cost_basis_usd', sa.Numeric(18, 2), nullable=False),
        sa.Column('cost_per_unit_usd', sa.Numeric(18, 8), nullable=False),
        sa.Column('acquired_at', sa.DateTime(), nullable=False),
        sa.Column('is_long_term', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tax_lots_asset', 'tax_lots', ['asset'])
    op.create_index('ix_tax_lots_acquired_at', 'tax_lots', ['acquired_at'])
    
    # Tax Lot Disposals
    op.create_table(
        'tax_lot_disposals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tax_lot_id', sa.Integer(), nullable=False),
        sa.Column('sell_transaction_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(28, 18), nullable=False),
        sa.Column('proceeds_usd', sa.Numeric(18, 2), nullable=False),
        sa.Column('cost_basis_usd', sa.Numeric(18, 2), nullable=False),
        sa.Column('gain_loss_usd', sa.Numeric(18, 2), nullable=False),
        sa.Column('is_long_term', sa.Boolean(), nullable=False),
        sa.Column('disposed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tax_lot_id'], ['tax_lots.id']),
        sa.ForeignKeyConstraint(['sell_transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Staking Positions
    op.create_table(
        'staking_positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(28, 18), nullable=False),
        sa.Column('apy', sa.Numeric(8, 4), nullable=True),
        sa.Column('rewards_earned', sa.Numeric(28, 18), nullable=False, default=0),
        sa.Column('rewards_claimed', sa.Numeric(28, 18), nullable=False, default=0),
        sa.Column('status', sa.Enum('active', 'unbonding', 'inactive', name='stakingstatus'), nullable=True),
        sa.Column('validator', sa.String(100), nullable=True),
        sa.Column('lock_period_days', sa.Integer(), nullable=True),
        sa.Column('unlock_date', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_staking_positions_asset', 'staking_positions', ['asset'])
    op.create_index('ix_staking_positions_exchange', 'staking_positions', ['exchange'])
    op.create_index('ix_staking_positions_status', 'staking_positions', ['status'])
    
    # Staking Rewards
    op.create_table(
        'staking_rewards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('position_id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(28, 18), nullable=False),
        sa.Column('value_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('reward_type', sa.String(50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['position_id'], ['staking_positions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # DeFi Positions
    op.create_table(
        'defi_positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(50), nullable=False),
        sa.Column('chain', sa.String(50), nullable=False),
        sa.Column('position_type', sa.String(50), nullable=False),
        sa.Column('wallet_address', sa.String(100), nullable=False),
        sa.Column('contract_address', sa.String(100), nullable=True),
        sa.Column('asset', sa.String(20), nullable=True),
        sa.Column('asset_amount', sa.Numeric(28, 18), nullable=True),
        sa.Column('asset2', sa.String(20), nullable=True),
        sa.Column('asset2_amount', sa.Numeric(28, 18), nullable=True),
        sa.Column('value_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('apy', sa.Numeric(8, 4), nullable=True),
        sa.Column('health_factor', sa.Numeric(8, 4), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_defi_positions_protocol', 'defi_positions', ['protocol'])
    op.create_index('ix_defi_positions_chain', 'defi_positions', ['chain'])
    op.create_index('ix_defi_positions_wallet', 'defi_positions', ['wallet_address'])
    
    # DCA Bots
    op.create_table(
        'dca_bots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('quote_asset', sa.String(20), nullable=False, default='USD'),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('next_execution_at', sa.DateTime(), nullable=True),
        sa.Column('last_execution_at', sa.DateTime(), nullable=True),
        sa.Column('total_invested', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('total_acquired', sa.Numeric(28, 18), nullable=False, default=0),
        sa.Column('execution_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_total', sa.Numeric(18, 2), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'completed', 'deleted', name='dcastatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dca_bots_status', 'dca_bots', ['status'])
    op.create_index('ix_dca_bots_next_execution', 'dca_bots', ['next_execution_at'])
    
    # DCA Executions
    op.create_table(
        'dca_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('bot_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('amount_invested', sa.Numeric(18, 2), nullable=False),
        sa.Column('amount_acquired', sa.Numeric(28, 18), nullable=False),
        sa.Column('price', sa.Numeric(18, 8), nullable=False),
        sa.Column('fee', sa.Numeric(18, 8), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['dca_bots.id']),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('alert_type', sa.Enum('price_above', 'price_below', 'percent_change', 'portfolio_value', name='alerttype'), nullable=False),
        sa.Column('asset', sa.String(20), nullable=True),
        sa.Column('threshold', sa.Numeric(18, 8), nullable=False),
        sa.Column('notification_channels', sa.String(200), nullable=False, default='app'),
        sa.Column('status', sa.Enum('active', 'triggered', 'disabled', name='alertstatus'), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.Column('triggered_value', sa.Numeric(18, 8), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), default=False),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_status', 'alerts', ['status'])
    op.create_index('ix_alerts_asset', 'alerts', ['asset'])
    
    # Alert Triggers
    op.create_table(
        'alert_triggers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('triggered_value', sa.Numeric(18, 8), nullable=False),
        sa.Column('notification_sent', sa.Boolean(), default=False),
        sa.Column('notification_channels', sa.String(200), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Portfolio Snapshots
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('total_value_usd', sa.Numeric(18, 2), nullable=False),
        sa.Column('total_cost_basis_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('unrealized_pnl_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('realized_pnl_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('spot_value_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('staking_value_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('defi_value_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('nft_value_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('snapshot_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_portfolio_snapshots_at', 'portfolio_snapshots', ['snapshot_at'])
    
    # Holding Snapshots
    op.create_table(
        'holding_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(28, 18), nullable=False),
        sa.Column('price_usd', sa.Numeric(18, 8), nullable=False),
        sa.Column('value_usd', sa.Numeric(18, 2), nullable=False),
        sa.Column('allocation_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_snapshot_id'], ['portfolio_snapshots.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_holding_snapshots_asset', 'holding_snapshots', ['asset'])
    
    # Price Snapshots
    op.create_table(
        'price_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('price_usd', sa.Numeric(18, 8), nullable=False),
        sa.Column('volume_24h_usd', sa.Numeric(24, 2), nullable=True),
        sa.Column('market_cap_usd', sa.Numeric(24, 2), nullable=True),
        sa.Column('change_24h_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('snapshot_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_price_snapshots_asset_at', 'price_snapshots', ['asset', 'snapshot_at'])


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('price_snapshots')
    op.drop_table('holding_snapshots')
    op.drop_table('portfolio_snapshots')
    op.drop_table('alert_triggers')
    op.drop_table('alerts')
    op.drop_table('dca_executions')
    op.drop_table('dca_bots')
    op.drop_table('defi_positions')
    op.drop_table('staking_rewards')
    op.drop_table('staking_positions')
    op.drop_table('tax_lot_disposals')
    op.drop_table('tax_lots')
    op.drop_table('transactions')
    op.drop_table('holdings')
    op.drop_table('exchange_connections')
    op.drop_table('portfolios')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS stakingstatus")
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS dcastatus")
    op.execute("DROP TYPE IF EXISTS costbasismethod")
