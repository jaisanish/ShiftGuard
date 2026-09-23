import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from backend.app.database.connection import Base, get_db
from backend.app.database.models import TaskModel, TelemetryModel
from backend.app.main import app

# In-memory SQLite engine for fast, isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all 8 database tables in the in-memory test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide a transactional database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_test_data(db_session):
    """Seed minimal test records into the in-memory database."""
    # Seed 2 tasks
    task1 = TaskModel(
        task_id="TSK-TEST-01",
        machine_id="CAT-797F-101",
        operator_id="OP-101",
        task_type="ORE_HAULING",
        weather="CLEAR",
        operator_skill="EXPERT",
        machine_age_years=3.2,
        estimated_time_min=50.0,
        actual_time_min=46.5,
        planned_start="2026-09-20T06:00:00Z",
        actual_start="2026-09-20T06:02:00Z",
        working_condition="NORMAL",
    )
    task2 = TaskModel(
        task_id="TSK-TEST-02",
        machine_id="CAT-6060-201",
        operator_id="OP-103",
        task_type="OVERBURDEN_REMOVAL",
        weather="RAIN",
        operator_skill="INTERMEDIATE",
        machine_age_years=2.1,
        estimated_time_min=75.0,
        actual_time_min=88.2,
        planned_start="2026-09-20T07:00:00Z",
        actual_start="2026-09-20T07:05:00Z",
        working_condition="MUDDY",
    )
    db_session.add(task1)
    db_session.add(task2)

    # Seed 3 telemetry records
    telem1 = TelemetryModel(
        timestamp="2026-09-20T06:00:00Z",
        machine_id="CAT-797F-101",
        operator_id="OP-101",
        engine_hours=8420.50,
        engine_rpm=1650.0,
        engine_load_pct=60.0,
        machine_speed_kmh=30.0,
        fuel_used_l=5.20,
        idling_time_min=1.0,
        load_cycles=2,
        operating_state="HAULING_LOADED",
        seatbelt_status="FASTENED",
        proximity_distance_m=35.0,
        gps_zone="HAUL_ROAD_NORTH",
        working_condition="NORMAL",
        coolant_temp_c=85.0,
        hydraulic_oil_temp_c=70.0,
        fault_code="NONE",
        task_id="TSK-TEST-01",
    )
    telem2 = TelemetryModel(
        timestamp="2026-09-20T06:01:00Z",
        machine_id="CAT-797F-101",
        operator_id="OP-101",
        engine_hours=8420.52,
        engine_rpm=1680.0,
        engine_load_pct=62.0,
        machine_speed_kmh=32.0,
        fuel_used_l=5.80,
        idling_time_min=1.0,
        load_cycles=2,
        operating_state="HAULING_LOADED",
        seatbelt_status="FASTENED",
        proximity_distance_m=36.0,
        gps_zone="HAUL_ROAD_NORTH",
        working_condition="NORMAL",
        coolant_temp_c=85.4,
        hydraulic_oil_temp_c=70.2,
        fault_code="NONE",
        task_id="TSK-TEST-01",
    )
    telem3 = TelemetryModel(
        timestamp="2026-09-20T06:00:00Z",
        machine_id="CAT-6060-201",
        operator_id="OP-103",
        engine_hours=5120.20,
        engine_rpm=1850.0,
        engine_load_pct=85.0,
        machine_speed_kmh=1.5,
        fuel_used_l=12.40,
        idling_time_min=0.0,
        load_cycles=5,
        operating_state="EXCAVATING",
        seatbelt_status="FASTENED",
        proximity_distance_m=12.0,
        gps_zone="PIT_FLOOR_BENCH_A",
        working_condition="MUDDY",
        coolant_temp_c=88.5,
        hydraulic_oil_temp_c=76.0,
        fault_code="NONE",
        task_id="TSK-TEST-02",
    )
    db_session.add(telem1)
    db_session.add(telem2)
    db_session.add(telem3)
    db_session.commit()
