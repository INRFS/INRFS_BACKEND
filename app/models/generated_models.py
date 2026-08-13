from typing import Optional
import datetime
import decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, String, Table, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class MasterAccountType(Base):
    __tablename__ = 'master_account_type'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='master_account_type_pkey'),
        UniqueConstraint('account_type_name', name='master_account_type_account_type_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_type_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_investor_bank_details: Mapped[list['TnInvestorBankDetails']] = relationship('TnInvestorBankDetails', back_populates='account_type')


class MasterInterestRate(Base):
    __tablename__ = 'master_interest_rate'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='master_interest_rate_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monthly_interest_rate: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))


class MasterInvestmentStatus(Base):
    __tablename__ = 'master_investment_status'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_master_investment_status_id'),
        UniqueConstraint('status_name', name='uq_master_investment_status_name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_investment: Mapped[list['TnInvestment']] = relationship('TnInvestment', back_populates='investment_status')


class MasterInvestmentTenure(Base):
    __tablename__ = 'master_investment_tenure'
    __table_args__ = (
        CheckConstraint('tenure_months > 0', name='chk_master_investment_tenure_months'),
        PrimaryKeyConstraint('id', name='pk_master_investment_tenure_id'),
        UniqueConstraint('tenure_months', name='uq_master_investment_tenure_months')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_investment: Mapped[list['TnInvestment']] = relationship('TnInvestment', back_populates='tenure')
    tn_tenure_extension_request_current_tenure: Mapped[list['TnTenureExtensionRequest']] = relationship('TnTenureExtensionRequest', foreign_keys='[TnTenureExtensionRequest.current_tenure_id]', back_populates='current_tenure')
    tn_tenure_extension_request_requested_tenure: Mapped[list['TnTenureExtensionRequest']] = relationship('TnTenureExtensionRequest', foreign_keys='[TnTenureExtensionRequest.requested_tenure_id]', back_populates='requested_tenure')


class MasterInvestorRequestStatus(Base):
    __tablename__ = 'master_investor_request_status'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='master_investor_request_status_pkey'),
        UniqueConstraint('status_name', name='master_investor_request_status_status_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_preclose_request: Mapped[list['TnPrecloseRequest']] = relationship('TnPrecloseRequest', back_populates='request_status')
    tn_tenure_extension_request: Mapped[list['TnTenureExtensionRequest']] = relationship('TnTenureExtensionRequest', back_populates='request_status')


class MasterKycStatus(Base):
    __tablename__ = 'master_kyc_status'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='master_kyc_status_pkey'),
        UniqueConstraint('kyc_status_name', name='master_kyc_status_kyc_status_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kyc_status_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_investor_registration: Mapped[list['TnInvestorRegistration']] = relationship('TnInvestorRegistration', back_populates='kyc_status')


class MasterPaymentMethod(Base):
    __tablename__ = 'master_payment_method'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_master_payment_method_id'),
        UniqueConstraint('payment_method_name', name='uq_master_payment_method_name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_method_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_investor_payments: Mapped[list['TnInvestorPayments']] = relationship('TnInvestorPayments', back_populates='payment_method')


class MasterPaymentStatus(Base):
    __tablename__ = 'master_payment_status'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_master_payment_status_id'),
        UniqueConstraint('payment_status_name', name='uq_master_payment_status_name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_interest_schedule: Mapped[list['TnInterestSchedule']] = relationship('TnInterestSchedule', back_populates='payment_status')
    tn_investor_payments: Mapped[list['TnInvestorPayments']] = relationship('TnInvestorPayments', back_populates='payment_status')


class MasterRole(Base):
    __tablename__ = 'master_role'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_master_role_id'),
        UniqueConstraint('role_name', name='uq_master_role_name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_application_user: Mapped[list['TnApplicationUser']] = relationship('TnApplicationUser', back_populates='role')


class MasterSettlementStatus(Base):
    __tablename__ = 'master_settlement_status'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_master_settlement_status_id'),
        UniqueConstraint('status_name', name='uq_master_settlement_status_name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_settlement: Mapped[list['TnSettlement']] = relationship('TnSettlement', back_populates='settlement_status')


class MasterState(Base):
    __tablename__ = 'master_state'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_master_state_id'),
        UniqueConstraint('state_name', name='uq_master_state_name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    master_branch: Mapped[list['MasterBranch']] = relationship('MasterBranch', back_populates='state')
    tn_investor_registration: Mapped[list['TnInvestorRegistration']] = relationship('TnInvestorRegistration', back_populates='state')


class MasterUserStatus(Base):
    __tablename__ = 'master_user_status'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_master_user_status_id'),
        UniqueConstraint('status_name', name='uq_master_user_status')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    tn_application_user: Mapped[list['TnApplicationUser']] = relationship('TnApplicationUser', back_populates='user_status')


t_vw_admin_recent_investments = Table(
    'vw_admin_recent_investments', Base.metadata,
    Column('investment_id', String(20)),
    Column('investor_id', String(20)),
    Column('investor_name', String(255)),
    Column('investment_amount', Numeric(18, 2)),
    Column('interest_rate', Numeric(5, 2)),
    Column('tenure_months', Integer),
    Column('investment_date', DateTime),
    Column('investment_status', String(100))
)


class MasterBranch(Base):
    __tablename__ = 'master_branch'
    __table_args__ = (
        ForeignKeyConstraint(['state_id'], ['master_state.id'], name='fk_master_branch_state'),
        PrimaryKeyConstraint('id', name='pk_master_branch_id'),
        UniqueConstraint('branch_name', name='uq_master_branch_name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_name: Mapped[str] = mapped_column(String(150), nullable=False)
    state_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    state: Mapped['MasterState'] = relationship('MasterState', back_populates='master_branch')
    tn_application_user: Mapped[list['TnApplicationUser']] = relationship('TnApplicationUser', back_populates='branch')
    tn_investor_registration: Mapped[list['TnInvestorRegistration']] = relationship('TnInvestorRegistration', back_populates='branch')
    tn_investor_registration_approval_history_new_branch: Mapped[list['TnInvestorRegistrationApprovalHistory']] = relationship('TnInvestorRegistrationApprovalHistory', foreign_keys='[TnInvestorRegistrationApprovalHistory.new_branch_id]', back_populates='new_branch')
    tn_investor_registration_approval_history_old_branch: Mapped[list['TnInvestorRegistrationApprovalHistory']] = relationship('TnInvestorRegistrationApprovalHistory', foreign_keys='[TnInvestorRegistrationApprovalHistory.old_branch_id]', back_populates='old_branch')


class TnApplicationUser(Base):
    __tablename__ = 'tn_application_user'
    __table_args__ = (
        ForeignKeyConstraint(['branch_id'], ['master_branch.id'], name='fk_tn_application_user_branch'),
        ForeignKeyConstraint(['role_id'], ['master_role.id'], name='fk_tn_application_user_role'),
        ForeignKeyConstraint(['user_status_id'], ['master_user_status.id'], name='fk_tn_application_user_status'),
        PrimaryKeyConstraint('id', name='pk_tn_application_user_id'),
        UniqueConstraint('mobile', name='uq_tn_application_user_mobile'),
        UniqueConstraint('username', name='uq_tn_application_user_username'),
        Index('uq_tn_application_user_email', 'email', postgresql_where='(email IS NOT NULL)', unique=True)
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[str] = mapped_column(String(20), nullable=False)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(100))
    password: Mapped[Optional[str]] = mapped_column(String(255))
    failed_login_attempts: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    last_login_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    branch: Mapped[Optional['MasterBranch']] = relationship('MasterBranch', back_populates='tn_application_user')
    role: Mapped['MasterRole'] = relationship('MasterRole', back_populates='tn_application_user')
    user_status: Mapped['MasterUserStatus'] = relationship('MasterUserStatus', back_populates='tn_application_user')
    tn_investor_registration_approved_by: Mapped[list['TnInvestorRegistration']] = relationship('TnInvestorRegistration', foreign_keys='[TnInvestorRegistration.approved_by]', back_populates='tn_application_user')
    tn_investor_registration_user: Mapped['TnInvestorRegistration'] = relationship('TnInvestorRegistration', uselist=False, foreign_keys='[TnInvestorRegistration.user_id]', back_populates='tn_application_user_user')
    tn_login_history: Mapped[list['TnLoginHistory']] = relationship('TnLoginHistory', back_populates='user')
    tn_otp_log: Mapped[list['TnOtpLog']] = relationship('TnOtpLog', back_populates='user')
    tn_password_reset: Mapped[list['TnPasswordReset']] = relationship('TnPasswordReset', back_populates='user')
    tn_investment_approved_by: Mapped[list['TnInvestment']] = relationship('TnInvestment', foreign_keys='[TnInvestment.approved_by]', back_populates='tn_application_user')
    tn_investment_created_by: Mapped[list['TnInvestment']] = relationship('TnInvestment', foreign_keys='[TnInvestment.created_by]', back_populates='tn_application_user_')
    tn_investment_modified_by: Mapped[list['TnInvestment']] = relationship('TnInvestment', foreign_keys='[TnInvestment.modified_by]', back_populates='tn_application_user1')
    tn_investor_registration_approval_history: Mapped[list['TnInvestorRegistrationApprovalHistory']] = relationship('TnInvestorRegistrationApprovalHistory', back_populates='tn_application_user')
    tn_bond_created_by: Mapped[list['TnBond']] = relationship('TnBond', foreign_keys='[TnBond.created_by]', back_populates='tn_application_user')
    tn_bond_modified_by: Mapped[list['TnBond']] = relationship('TnBond', foreign_keys='[TnBond.modified_by]', back_populates='tn_application_user_')
    tn_interest_schedule_created_by: Mapped[list['TnInterestSchedule']] = relationship('TnInterestSchedule', foreign_keys='[TnInterestSchedule.created_by]', back_populates='tn_application_user')
    tn_interest_schedule_modified_by: Mapped[list['TnInterestSchedule']] = relationship('TnInterestSchedule', foreign_keys='[TnInterestSchedule.modified_by]', back_populates='tn_application_user_')
    tn_investor_payments_created_by: Mapped[list['TnInvestorPayments']] = relationship('TnInvestorPayments', foreign_keys='[TnInvestorPayments.created_by]', back_populates='tn_application_user')
    tn_investor_payments_modified_by: Mapped[list['TnInvestorPayments']] = relationship('TnInvestorPayments', foreign_keys='[TnInvestorPayments.modified_by]', back_populates='tn_application_user_')
    tn_preclose_request_approved_by: Mapped[list['TnPrecloseRequest']] = relationship('TnPrecloseRequest', foreign_keys='[TnPrecloseRequest.approved_by]', back_populates='tn_application_user')
    tn_preclose_request_created_by: Mapped[list['TnPrecloseRequest']] = relationship('TnPrecloseRequest', foreign_keys='[TnPrecloseRequest.created_by]', back_populates='tn_application_user_')
    tn_preclose_request_modified_by: Mapped[list['TnPrecloseRequest']] = relationship('TnPrecloseRequest', foreign_keys='[TnPrecloseRequest.modified_by]', back_populates='tn_application_user1')
    tn_settlement_approved_by: Mapped[list['TnSettlement']] = relationship('TnSettlement', foreign_keys='[TnSettlement.approved_by]', back_populates='tn_application_user')
    tn_settlement_created_by: Mapped[list['TnSettlement']] = relationship('TnSettlement', foreign_keys='[TnSettlement.created_by]', back_populates='tn_application_user_')
    tn_settlement_modified_by: Mapped[list['TnSettlement']] = relationship('TnSettlement', foreign_keys='[TnSettlement.modified_by]', back_populates='tn_application_user1')
    tn_settlement_paid_by: Mapped[list['TnSettlement']] = relationship('TnSettlement', foreign_keys='[TnSettlement.paid_by]', back_populates='tn_application_user2')
    tn_tenure_extension_request_approved_by: Mapped[list['TnTenureExtensionRequest']] = relationship('TnTenureExtensionRequest', foreign_keys='[TnTenureExtensionRequest.approved_by]', back_populates='tn_application_user')
    tn_tenure_extension_request_created_by: Mapped[list['TnTenureExtensionRequest']] = relationship('TnTenureExtensionRequest', foreign_keys='[TnTenureExtensionRequest.created_by]', back_populates='tn_application_user_')
    tn_tenure_extension_request_modified_by: Mapped[list['TnTenureExtensionRequest']] = relationship('TnTenureExtensionRequest', foreign_keys='[TnTenureExtensionRequest.modified_by]', back_populates='tn_application_user1')


class TnInvestorRegistration(Base):
    __tablename__ = 'tn_investor_registration'
    __table_args__ = (
        ForeignKeyConstraint(['approved_by'], ['tn_application_user.id'], name='fk_tn_investor_registration_approved_by'),
        ForeignKeyConstraint(['branch_id'], ['master_branch.id'], name='fk_tn_investor_registration_branch'),
        ForeignKeyConstraint(['kyc_status_id'], ['master_kyc_status.id'], name='fk_tn_investor_registration_kyc_status'),
        ForeignKeyConstraint(['state_id'], ['master_state.id'], name='fk_tn_investor_registration_state'),
        ForeignKeyConstraint(['user_id'], ['tn_application_user.id'], name='fk_tn_investor_registration_user'),
        PrimaryKeyConstraint('id', name='pk_tn_investor_registration_id'),
        UniqueConstraint('aadhaar_number', name='uq_tn_investor_registration_aadhaar'),
        UniqueConstraint('investor_id', name='uq_tn_investor_registration_investor_id'),
        UniqueConstraint('user_id', name='uq_tn_investor_registration_user')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date_of_birth: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    aadhaar_number: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state_id: Mapped[int] = mapped_column(Integer, nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    kyc_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    investor_id: Mapped[Optional[str]] = mapped_column(String(20))
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    approved_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remarks: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    tn_application_user: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[approved_by], back_populates='tn_investor_registration_approved_by')
    branch: Mapped['MasterBranch'] = relationship('MasterBranch', back_populates='tn_investor_registration')
    kyc_status: Mapped['MasterKycStatus'] = relationship('MasterKycStatus', back_populates='tn_investor_registration')
    state: Mapped['MasterState'] = relationship('MasterState', back_populates='tn_investor_registration')
    tn_application_user_user: Mapped['TnApplicationUser'] = relationship('TnApplicationUser', foreign_keys=[user_id], back_populates='tn_investor_registration_user')
    tn_investment: Mapped[list['TnInvestment']] = relationship('TnInvestment', back_populates='investor_registration')
    tn_investor_bank_details: Mapped[list['TnInvestorBankDetails']] = relationship('TnInvestorBankDetails', back_populates='investor')
    tn_investor_registration_approval_history: Mapped[list['TnInvestorRegistrationApprovalHistory']] = relationship('TnInvestorRegistrationApprovalHistory', back_populates='investor_registration')


class TnLoginHistory(Base):
    __tablename__ = 'tn_login_history'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['tn_application_user.id'], name='fk_tn_login_history_user_id'),
        PrimaryKeyConstraint('id', name='pk_tn_login_history_id'),
        Index('idx_tn_login_history_login_date', 'login_date'),
        Index('idx_tn_login_history_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    login_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    logout_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    login_type: Mapped[Optional[str]] = mapped_column(String(50))
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user: Mapped['TnApplicationUser'] = relationship('TnApplicationUser', back_populates='tn_login_history')


class TnOtpLog(Base):
    __tablename__ = 'tn_otp_log'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['tn_application_user.id'], name='fk_tn_otp_log_user_id'),
        PrimaryKeyConstraint('id', name='pk_tn_otp_log_id'),
        Index('idx_tn_otp_log_expiry_date', 'expiry_date'),
        Index('idx_tn_otp_log_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    otp: Mapped[str] = mapped_column(String(10), nullable=False)
    expiry_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    generated_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    verified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    is_verified: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user: Mapped['TnApplicationUser'] = relationship('TnApplicationUser', back_populates='tn_otp_log')


class TnPasswordReset(Base):
    __tablename__ = 'tn_password_reset'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['tn_application_user.id'], name='fk_tn_password_reset_user_id'),
        PrimaryKeyConstraint('id', name='pk_tn_password_reset_id'),
        Index('idx_tn_password_reset_token', 'reset_token'),
        Index('idx_tn_password_reset_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reset_token: Mapped[str] = mapped_column(String(255), nullable=False)
    expiry_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    used_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user: Mapped['TnApplicationUser'] = relationship('TnApplicationUser', back_populates='tn_password_reset')


class TnInvestment(Base):
    __tablename__ = 'tn_investment'
    __table_args__ = (
        CheckConstraint('interest_rate >= 0::numeric', name='chk_tn_investment_interest'),
        CheckConstraint('investment_amount > 0::numeric', name='chk_tn_investment_amount'),
        ForeignKeyConstraint(['approved_by'], ['tn_application_user.id'], name='fk_tn_investment_approved_by'),
        ForeignKeyConstraint(['created_by'], ['tn_application_user.id'], name='fk_tn_investment_created_by'),
        ForeignKeyConstraint(['investment_status_id'], ['master_investment_status.id'], name='fk_tn_investment_status'),
        ForeignKeyConstraint(['investor_registration_id'], ['tn_investor_registration.id'], name='fk_tn_investment_investor_registration'),
        ForeignKeyConstraint(['modified_by'], ['tn_application_user.id'], name='fk_tn_investment_modified_by'),
        ForeignKeyConstraint(['tenure_id'], ['master_investment_tenure.id'], name='fk_tn_investment_tenure'),
        PrimaryKeyConstraint('id', name='pk_tn_investment_id'),
        UniqueConstraint('investment_id', name='uq_tn_investment_number')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investor_registration_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tenure_id: Mapped[int] = mapped_column(Integer, nullable=False)
    investment_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_rate: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    expected_interest_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    maturity_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    investment_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    investment_id: Mapped[Optional[str]] = mapped_column(String(20))
    investment_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    maturity_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    approved_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remarks: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    tn_application_user: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[approved_by], back_populates='tn_investment_approved_by')
    tn_application_user_: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[created_by], back_populates='tn_investment_created_by')
    investment_status: Mapped['MasterInvestmentStatus'] = relationship('MasterInvestmentStatus', back_populates='tn_investment')
    investor_registration: Mapped['TnInvestorRegistration'] = relationship('TnInvestorRegistration', back_populates='tn_investment')
    tn_application_user1: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[modified_by], back_populates='tn_investment_modified_by')
    tenure: Mapped['MasterInvestmentTenure'] = relationship('MasterInvestmentTenure', back_populates='tn_investment')
    tn_bond: Mapped['TnBond'] = relationship('TnBond', uselist=False, back_populates='investment')
    tn_interest_schedule: Mapped[list['TnInterestSchedule']] = relationship('TnInterestSchedule', back_populates='investment')
    tn_investor_payments: Mapped[list['TnInvestorPayments']] = relationship('TnInvestorPayments', back_populates='investment')
    tn_preclose_request: Mapped[list['TnPrecloseRequest']] = relationship('TnPrecloseRequest', back_populates='investment')
    tn_settlement: Mapped[list['TnSettlement']] = relationship('TnSettlement', back_populates='investment')
    tn_tenure_extension_request: Mapped[list['TnTenureExtensionRequest']] = relationship('TnTenureExtensionRequest', back_populates='investment')


class TnInvestorBankDetails(Base):
    __tablename__ = 'tn_investor_bank_details'
    __table_args__ = (
        ForeignKeyConstraint(['account_type_id'], ['master_account_type.id'], name='fk_investor_bank_details_account_type_id'),
        ForeignKeyConstraint(['investor_id'], ['tn_investor_registration.id'], name='fk_investor_bank_details_investor'),
        PrimaryKeyConstraint('id', name='tn_investor_bank_details_pkey')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investor_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_holder_name: Mapped[str] = mapped_column(String(150), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    account_number: Mapped[str] = mapped_column(String(30), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    account_type: Mapped['MasterAccountType'] = relationship('MasterAccountType', back_populates='tn_investor_bank_details')
    investor: Mapped['TnInvestorRegistration'] = relationship('TnInvestorRegistration', back_populates='tn_investor_bank_details')
    tn_investor_payments: Mapped[list['TnInvestorPayments']] = relationship('TnInvestorPayments', back_populates='investor_bank_details')


class TnInvestorRegistrationApprovalHistory(Base):
    __tablename__ = 'tn_investor_registration_approval_history'
    __table_args__ = (
        ForeignKeyConstraint(['action_by'], ['tn_application_user.id'], name='fk_tn_investor_registration_history_action_by'),
        ForeignKeyConstraint(['investor_registration_id'], ['tn_investor_registration.id'], name='fk_tn_investor_registration_history_registration'),
        ForeignKeyConstraint(['new_branch_id'], ['master_branch.id'], name='fk_tn_investor_registration_history_new_branch'),
        ForeignKeyConstraint(['old_branch_id'], ['master_branch.id'], name='fk_tn_investor_registration_history_old_branch'),
        PrimaryKeyConstraint('id', name='pk_tn_investor_registration_approval_history_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investor_registration_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    action_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    old_branch_id: Mapped[Optional[int]] = mapped_column(Integer)
    new_branch_id: Mapped[Optional[int]] = mapped_column(Integer)
    remarks: Mapped[Optional[str]] = mapped_column(String(500))
    action_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    tn_application_user: Mapped['TnApplicationUser'] = relationship('TnApplicationUser', back_populates='tn_investor_registration_approval_history')
    investor_registration: Mapped['TnInvestorRegistration'] = relationship('TnInvestorRegistration', back_populates='tn_investor_registration_approval_history')
    new_branch: Mapped[Optional['MasterBranch']] = relationship('MasterBranch', foreign_keys=[new_branch_id], back_populates='tn_investor_registration_approval_history_new_branch')
    old_branch: Mapped[Optional['MasterBranch']] = relationship('MasterBranch', foreign_keys=[old_branch_id], back_populates='tn_investor_registration_approval_history_old_branch')


class TnBond(Base):
    __tablename__ = 'tn_bond'
    __table_args__ = (
        ForeignKeyConstraint(['created_by'], ['tn_application_user.id'], name='fk_tn_bond_created_by'),
        ForeignKeyConstraint(['investment_id'], ['tn_investment.id'], name='fk_tn_bond_investment'),
        ForeignKeyConstraint(['modified_by'], ['tn_application_user.id'], name='fk_tn_bond_modified_by'),
        PrimaryKeyConstraint('id', name='pk_tn_bond_id'),
        UniqueConstraint('bond_id', name='uq_tn_bond_id'),
        UniqueConstraint('investment_id', name='uq_tn_bond_investment')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bond_id: Mapped[str] = mapped_column(String(20), nullable=False)
    investment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    maturity_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    issue_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    remarks: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    tn_application_user: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[created_by], back_populates='tn_bond_created_by')
    investment: Mapped['TnInvestment'] = relationship('TnInvestment', back_populates='tn_bond')
    tn_application_user_: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[modified_by], back_populates='tn_bond_modified_by')


class TnInterestSchedule(Base):
    __tablename__ = 'tn_interest_schedule'
    __table_args__ = (
        ForeignKeyConstraint(['created_by'], ['tn_application_user.id'], name='fk_tn_interest_schedule_created_by'),
        ForeignKeyConstraint(['investment_id'], ['tn_investment.id'], name='fk_tn_interest_schedule_investmen'),
        ForeignKeyConstraint(['modified_by'], ['tn_application_user.id'], name='fk_tn_interest_schedule_modified_by'),
        ForeignKeyConstraint(['payment_status_id'], ['master_payment_status.id'], name='fk_tn_interest_schedule_payment_status'),
        PrimaryKeyConstraint('id', name='pk_tn_interest_schedule_id'),
        UniqueConstraint('investment_id', 'interest_month', name='uq_tn_interest_schedule')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    interest_month: Mapped[int] = mapped_column(Integer, nullable=False)
    interest_due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    interest_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    payment_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    interest_paid_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    gst_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(18, 2))
    net_interest_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(18, 2))

    tn_application_user: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[created_by], back_populates='tn_interest_schedule_created_by')
    investment: Mapped['TnInvestment'] = relationship('TnInvestment', back_populates='tn_interest_schedule')
    tn_application_user_: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[modified_by], back_populates='tn_interest_schedule_modified_by')
    payment_status: Mapped['MasterPaymentStatus'] = relationship('MasterPaymentStatus', back_populates='tn_interest_schedule')


class TnInvestorPayments(Base):
    __tablename__ = 'tn_investor_payments'
    __table_args__ = (
        CheckConstraint('payment_amount > 0::numeric', name='chk_tn_investor_payments_amount'),
        ForeignKeyConstraint(['created_by'], ['tn_application_user.id'], name='fk_tn_investor_payments_created_by'),
        ForeignKeyConstraint(['investment_id'], ['tn_investment.id'], name='fk_tn_investor_payments_investment'),
        ForeignKeyConstraint(['investor_bank_details_id'], ['tn_investor_bank_details.id'], name='fk_tn_investor_payments_investor_bank_details'),
        ForeignKeyConstraint(['modified_by'], ['tn_application_user.id'], name='fk_tn_investor_payments_modified_by'),
        ForeignKeyConstraint(['payment_method_id'], ['master_payment_method.id'], name='fk_tn_investor_payments_payment_method'),
        ForeignKeyConstraint(['payment_status_id'], ['master_payment_status.id'], name='fk_tn_investor_payments_payment_status'),
        PrimaryKeyConstraint('id', name='pk_tn_investor_payments_id'),
        UniqueConstraint('utr_number', name='uq_tn_investor_payments_utr_number')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payment_method_id: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    utr_number: Mapped[str] = mapped_column(String(100), nullable=False)
    investor_bank_details_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    payment_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    remarks: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    tn_application_user: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[created_by], back_populates='tn_investor_payments_created_by')
    investment: Mapped['TnInvestment'] = relationship('TnInvestment', back_populates='tn_investor_payments')
    investor_bank_details: Mapped[Optional['TnInvestorBankDetails']] = relationship('TnInvestorBankDetails', back_populates='tn_investor_payments')
    tn_application_user_: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[modified_by], back_populates='tn_investor_payments_modified_by')
    payment_method: Mapped['MasterPaymentMethod'] = relationship('MasterPaymentMethod', back_populates='tn_investor_payments')
    payment_status: Mapped['MasterPaymentStatus'] = relationship('MasterPaymentStatus', back_populates='tn_investor_payments')


class TnPrecloseRequest(Base):
    __tablename__ = 'tn_preclose_request'
    __table_args__ = (
        ForeignKeyConstraint(['approved_by'], ['tn_application_user.id'], name='fk_tn_preclose_request_approved_by'),
        ForeignKeyConstraint(['created_by'], ['tn_application_user.id'], name='fk_tn_preclose_request_created_by'),
        ForeignKeyConstraint(['investment_id'], ['tn_investment.id'], name='fk_tn_preclose_request_investment'),
        ForeignKeyConstraint(['modified_by'], ['tn_application_user.id'], name='fk_tn_preclose_request_modified_by'),
        ForeignKeyConstraint(['request_status_id'], ['master_investor_request_status.id'], name='fk_tn_preclose_request_status'),
        PrimaryKeyConstraint('id', name='pk_tn_preclose_request_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    request_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    preclose_reason: Mapped[Optional[str]] = mapped_column(String(500))
    requested_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    approved_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remarks: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    tn_application_user: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[approved_by], back_populates='tn_preclose_request_approved_by')
    tn_application_user_: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[created_by], back_populates='tn_preclose_request_created_by')
    investment: Mapped['TnInvestment'] = relationship('TnInvestment', back_populates='tn_preclose_request')
    tn_application_user1: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[modified_by], back_populates='tn_preclose_request_modified_by')
    request_status: Mapped['MasterInvestorRequestStatus'] = relationship('MasterInvestorRequestStatus', back_populates='tn_preclose_request')


class TnSettlement(Base):
    __tablename__ = 'tn_settlement'
    __table_args__ = (
        CheckConstraint("settlement_type::text = ANY (ARRAY['TENURE_TIMEOUT'::character varying::text, 'PRECLOSE'::character varying::text])", name='chk_tn_settlement_type'),
        ForeignKeyConstraint(['approved_by'], ['tn_application_user.id'], name='fk_tn_settlement_approved_by'),
        ForeignKeyConstraint(['created_by'], ['tn_application_user.id'], name='fk_tn_settlement_created_by'),
        ForeignKeyConstraint(['investment_id'], ['tn_investment.id'], name='fk_tn_settlement_investment'),
        ForeignKeyConstraint(['modified_by'], ['tn_application_user.id'], name='fk_tn_settlement_modified_by'),
        ForeignKeyConstraint(['paid_by'], ['tn_application_user.id'], name='fk_tn_settlement_paid_by'),
        ForeignKeyConstraint(['settlement_status_id'], ['master_settlement_status.id'], name='fk_tn_settlement_status'),
        PrimaryKeyConstraint('id', name='pk_tn_settlement_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    settlement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    principal_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_settlement_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    settlement_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    penalty_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(18, 2), server_default=text('0'))
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    approved_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    paid_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    paid_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remarks: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    gst_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(18, 2))

    tn_application_user: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[approved_by], back_populates='tn_settlement_approved_by')
    tn_application_user_: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[created_by], back_populates='tn_settlement_created_by')
    investment: Mapped['TnInvestment'] = relationship('TnInvestment', back_populates='tn_settlement')
    tn_application_user1: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[modified_by], back_populates='tn_settlement_modified_by')
    tn_application_user2: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[paid_by], back_populates='tn_settlement_paid_by')
    settlement_status: Mapped['MasterSettlementStatus'] = relationship('MasterSettlementStatus', back_populates='tn_settlement')


class TnTenureExtensionRequest(Base):
    __tablename__ = 'tn_tenure_extension_request'
    __table_args__ = (
        ForeignKeyConstraint(['approved_by'], ['tn_application_user.id'], name='fk_tn_tenure_extension_request_approved_by'),
        ForeignKeyConstraint(['created_by'], ['tn_application_user.id'], name='fk_tn_tenure_extension_request_created_by'),
        ForeignKeyConstraint(['current_tenure_id'], ['master_investment_tenure.id'], name='fk_tn_tenure_extension_request_current_tenure'),
        ForeignKeyConstraint(['investment_id'], ['tn_investment.id'], name='fk_tn_tenure_extension_request_investment'),
        ForeignKeyConstraint(['modified_by'], ['tn_application_user.id'], name='fk_tn_tenure_extension_request_modified_by'),
        ForeignKeyConstraint(['request_status_id'], ['master_investor_request_status.id'], name='fk_tn_tenure_extension_request_status'),
        ForeignKeyConstraint(['requested_tenure_id'], ['master_investment_tenure.id'], name='fk_tn_tenure_extension_request_requested_tenure'),
        PrimaryKeyConstraint('id', name='pk_tn_tenure_extension_request_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_tenure_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_tenure_id: Mapped[int] = mapped_column(Integer, nullable=False)
    request_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    approved_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remarks: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    modified_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    tn_application_user: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[approved_by], back_populates='tn_tenure_extension_request_approved_by')
    tn_application_user_: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[created_by], back_populates='tn_tenure_extension_request_created_by')
    current_tenure: Mapped['MasterInvestmentTenure'] = relationship('MasterInvestmentTenure', foreign_keys=[current_tenure_id], back_populates='tn_tenure_extension_request_current_tenure')
    investment: Mapped['TnInvestment'] = relationship('TnInvestment', back_populates='tn_tenure_extension_request')
    tn_application_user1: Mapped[Optional['TnApplicationUser']] = relationship('TnApplicationUser', foreign_keys=[modified_by], back_populates='tn_tenure_extension_request_modified_by')
    request_status: Mapped['MasterInvestorRequestStatus'] = relationship('MasterInvestorRequestStatus', back_populates='tn_tenure_extension_request')
    requested_tenure: Mapped['MasterInvestmentTenure'] = relationship('MasterInvestmentTenure', foreign_keys=[requested_tenure_id], back_populates='tn_tenure_extension_request_requested_tenure')
