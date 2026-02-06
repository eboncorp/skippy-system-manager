"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-02-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    
    # Portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('total_value_usd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('total_cost_basis_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('total_staking_value_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('total_defi_value_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('total_nft_value_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('holdings_by_asset', sa.JSON(), nullable=True),
        sa.Column('holdings_by_exchange', sa.JSON(), nullable=True),
        sa.Column('snapshot_type', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_portfolios_timestamp', 'portfolios', ['timestamp'], unique=False)
    op.create_index('ix_portfolios_timestamp_type', 'portfolios', ['timestamp', 'snapshot_type'], unique=False)
    
    # Transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('transaction_type', sa.Enum('buy', 'sell', 'transfer_in', 'transfer_out', 'stake', 'unstake', 'reward', 'fee', 'airdrop', 'fork', name='transactiontype'), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=30, scale=18), nullable=False),
        sa.Column('price_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('total_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('fee_amount', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('fee_currency', sa.String(length=20), nullable=True),
        sa.Column('fee_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('exchange', sa.String(length=50), nullable=True),
        sa.Column('wallet_address', sa.String(length=100), nullable=True),
        sa.Column('counterparty', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_asset', 'transactions', ['asset'], unique=False)
    op.create_index('ix_transactions_exchange', 'transactions', ['exchange'], unique=False)
    op.create_index('ix_transactions_external_id', 'transactions', ['external_id'], unique=False)
    op.create_index('ix_transactions_timestamp', 'transactions', ['timestamp'], unique=False)
    op.create_index('ix_transactions_transaction_type', 'transactions', ['transaction_type'], unique=False)
    op.create_index('ix_transactions_asset_timestamp', 'transactions', ['asset', 'timestamp'], unique=False)
    op.create_index('ix_transactions_exchange_timestamp', 'transactions', ['exchange', 'timestamp'], unique=False)
    
    # Tax Lots table
    op.create_table(
        'tax_lots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=30, scale=18), nullable=False),
        sa.Column('remaining_amount', sa.Numeric(precision=30, scale=18), nullable=False),
        sa.Column('cost_basis_usd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('cost_basis_per_unit', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('acquired_at', sa.DateTime(), nullable=False),
        sa.Column('exchange', sa.String(length=50), nullable=True),
        sa.Column('disposed_at', sa.DateTime(), nullable=True),
        sa.Column('proceeds_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('gain_loss_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('is_long_term', sa.Boolean(), nullable=True),
        sa.Column('is_closed', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tax_lots_asset', 'tax_lots', ['asset'], unique=False)
    op.create_index('ix_tax_lots_acquired_at', 'tax_lots', ['acquired_at'], unique=False)
    op.create_index('ix_tax_lots_is_closed', 'tax_lots', ['is_closed'], unique=False)
    op.create_index('ix_tax_lots_asset_acquired', 'tax_lots', ['asset', 'acquired_at'], unique=False)
    op.create_index('ix_tax_lots_open', 'tax_lots', ['asset', 'is_closed', 'acquired_at'], unique=False)
    
    # Staking Positions table
    op.create_table(
        'staking_positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('exchange', sa.String(length=50), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=30, scale=18), nullable=False),
        sa.Column('apy', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('rewards_earned', sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column('rewards_claimed', sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column('status', sa.Enum('active', 'unbonding', 'completed', name='stakingstatus'), nullable=True),
        sa.Column('validator', sa.String(length=200), nullable=True),
        sa.Column('staked_at', sa.DateTime(), nullable=False),
        sa.Column('unbonding_at', sa.DateTime(), nullable=True),
        sa.Column('unstaked_at', sa.DateTime(), nullable=True),
        sa.Column('lock_period_days', sa.Integer(), nullable=True),
        sa.Column('unlock_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_staking_positions_asset', 'staking_positions', ['asset'], unique=False)
    op.create_index('ix_staking_positions_exchange', 'staking_positions', ['exchange'], unique=False)
    op.create_index('ix_staking_positions_status', 'staking_positions', ['status'], unique=False)
    op.create_index('ix_staking_exchange_asset', 'staking_positions', ['exchange', 'asset'], unique=False)
    
    # DCA Bots table
    op.create_table(
        'dca_bots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('exchange', sa.String(length=50), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('quote_currency', sa.String(length=20), nullable=True),
        sa.Column('amount_per_execution', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('max_total_amount', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('max_executions', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'completed', 'deleted', name='dcastatus'), nullable=True),
        sa.Column('total_invested', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('total_acquired', sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=True),
        sa.Column('average_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('next_execution_at', sa.DateTime(), nullable=True),
        sa.Column('last_execution_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dca_bots_status', 'dca_bots', ['status'], unique=False)
    op.create_index('ix_dca_bots_next_execution_at', 'dca_bots', ['next_execution_at'], unique=False)
    
    # DCA Executions table
    op.create_table(
        'dca_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('bot_id', sa.Integer(), nullable=False),
        sa.Column('amount_usd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('amount_acquired', sa.Numeric(precision=30, scale=18), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('fee_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('order_id', sa.String(length=100), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['dca_bots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dca_executions_executed_at', 'dca_executions', ['executed_at'], unique=False)
    
    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_type', sa.Enum('price_above', 'price_below', 'percent_change', 'portfolio_value', name='alerttype'), nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=True),
        sa.Column('threshold', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('comparison', sa.String(length=10), nullable=True),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('active', 'triggered', 'disabled', name='alertstatus'), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('last_value', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('note', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_status', 'alerts', ['status'], unique=False)
    
    # Alert Triggers table
    op.create_table(
        'alert_triggers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('triggered_value', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('threshold', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('notifications_sent', sa.JSON(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_triggers_triggered_at', 'alert_triggers', ['triggered_at'], unique=False)
    
    # Wallets table
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('address', sa.String(length=100), nullable=False),
        sa.Column('chain', sa.String(length=20), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.Column('track_transactions', sa.Boolean(), nullable=True),
        sa.Column('track_defi', sa.Boolean(), nullable=True),
        sa.Column('track_nfts', sa.Boolean(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('last_block_synced', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('address')
    )
    op.create_index('ix_wallets_chain_address', 'wallets', ['chain', 'address'], unique=False)
    
    # DeFi Positions table
    op.create_table(
        'defi_positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('protocol', sa.String(length=50), nullable=False),
        sa.Column('chain', sa.String(length=20), nullable=False),
        sa.Column('wallet_address', sa.String(length=100), nullable=False),
        sa.Column('position_type', sa.String(length=30), nullable=False),
        sa.Column('pool_address', sa.String(length=100), nullable=True),
        sa.Column('pool_name', sa.String(length=100), nullable=True),
        sa.Column('asset', sa.String(length=20), nullable=True),
        sa.Column('amount', sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column('token0', sa.String(length=20), nullable=True),
        sa.Column('token1', sa.String(length=20), nullable=True),
        sa.Column('token0_amount', sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column('token1_amount', sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column('value_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('apy', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('health_factor', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('impermanent_loss_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('earnings_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('fees_earned_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('rewards_earned_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_defi_positions_protocol', 'defi_positions', ['protocol'], unique=False)
    op.create_index('ix_defi_positions_wallet_address', 'defi_positions', ['wallet_address'], unique=False)
    op.create_index('ix_defi_protocol_wallet', 'defi_positions', ['protocol', 'wallet_address'], unique=False)
    
    # Price Cache table
    op.create_table(
        'price_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset', sa.String(length=20), nullable=False),
        sa.Column('price_usd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('price_24h_ago', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('change_24h_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('high_24h', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('low_24h', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('volume_24h_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('market_cap_usd', sa.Numeric(precision=30, scale=8), nullable=True),
        sa.Column('circulating_supply', sa.Numeric(precision=30, scale=8), nullable=True),
        sa.Column('source', sa.String(length=30), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset', name='uq_price_cache_asset')
    )
    op.create_index('ix_price_cache_asset', 'price_cache', ['asset'], unique=False)
    op.create_index('ix_price_cache_updated_at', 'price_cache', ['updated_at'], unique=False)
    
    # Settings table
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('settings')
    op.drop_table('price_cache')
    op.drop_table('defi_positions')
    op.drop_table('wallets')
    op.drop_table('alert_triggers')
    op.drop_table('alerts')
    op.drop_table('dca_executions')
    op.drop_table('dca_bots')
    op.drop_table('staking_positions')
    op.drop_table('tax_lots')
    op.drop_table('transactions')
    op.drop_table('portfolios')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS stakingstatus")
    op.execute("DROP TYPE IF EXISTS dcastatus")
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.execute("DROP TYPE IF EXISTS alertstatus")
