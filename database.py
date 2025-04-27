import os
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

# Create SQLAlchemy base
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    locations = relationship("SavedLocation", back_populates="user", cascade="all, delete-orphan")
    crop_preferences = relationship("CropPreference", back_populates="user", cascade="all, delete-orphan")

class SavedLocation(Base):
    __tablename__ = 'saved_locations'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    is_default = Column(Boolean, default=False)
    user = relationship("User", back_populates="locations")

class CropPreference(Base):
    __tablename__ = 'crop_preferences'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    crop_name = Column(String(255))
    is_favorite = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    user = relationship("User", back_populates="crop_preferences")

class WeatherRecord(Base):
    __tablename__ = 'weather_records'
    
    id = Column(Integer, primary_key=True)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String(255), nullable=True)
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall = Column(Float, nullable=True)
    description = Column(String(255), nullable=True)

class SoilMoistureSensor(Base):
    __tablename__ = 'soil_moisture_sensors'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    name = Column(String(255))
    sensor_id = Column(String(255), unique=True)
    location_name = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    field_area = Column(String(255), nullable=True)
    depth = Column(Float, nullable=True)  # Depth in cm
    sensor_type = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", backref="soil_sensors")
    readings = relationship("SoilMoistureReading", back_populates="sensor", cascade="all, delete-orphan")
    
class SoilMoistureReading(Base):
    __tablename__ = 'soil_moisture_readings'
    
    id = Column(Integer, primary_key=True)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)
    sensor_id = Column(Integer, ForeignKey('soil_moisture_sensors.id'))
    moisture_percentage = Column(Float)  # Value between 0-100
    temperature = Column(Float, nullable=True)  # Soil temperature in Celsius
    electrical_conductivity = Column(Float, nullable=True)  # EC value in µS/cm
    battery_level = Column(Float, nullable=True)  # Percentage of battery remaining
    signal_strength = Column(Integer, nullable=True)  # Signal strength in dBm
    
    sensor = relationship("SoilMoistureSensor", back_populates="readings")

# Database connection setup
def get_engine():
    """Get database engine using environment variables"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback for local development
        db_url = "sqlite:///farmweather.db"
    return create_engine(db_url)

def init_db():
    """Initialize database with tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Create a new database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

# User management functions
def get_or_create_user(email=None, name=None):
    """Get existing user or create a new one"""
    session = get_session()
    
    try:
        if email:
            user = session.query(User).filter_by(email=email).first()
            if user:
                # Make a copy of the id before returning
                user_id = user.id
                return {'id': user_id, 'email': email, 'name': name}
        
        # Create new user
        user = User(email=email, name=name)
        session.add(user)
        session.commit()
        
        # Get the id and return a dictionary instead of the ORM object
        user_id = user.id
        return {'id': user_id, 'email': email, 'name': name}
    finally:
        session.close()

def save_location(user_id, name, latitude, longitude, is_default=False):
    """Save a location for a user"""
    session = get_session()
    
    try:
        # If this is the new default, unset any existing defaults
        if is_default:
            existing_defaults = session.query(SavedLocation).filter_by(
                user_id=user_id, is_default=True
            ).all()
            for loc in existing_defaults:
                loc.is_default = False
        
        location = SavedLocation(
            user_id=user_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
            is_default=is_default
        )
        session.add(location)
        session.commit()
        
        # Create a dictionary with the location data to return
        location_data = {
            'id': location.id,
            'name': location.name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'is_default': location.is_default
        }
        return location_data
    finally:
        session.close()

def get_saved_locations(user_id):
    """Get all saved locations for a user"""
    session = get_session()
    try:
        locations = session.query(SavedLocation).filter_by(user_id=user_id).all()
        # Convert to list of dictionaries to avoid session issues
        return [
            {
                'id': loc.id,
                'name': loc.name,
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'is_default': loc.is_default
            } 
            for loc in locations
        ]
    finally:
        session.close()

def get_default_location(user_id):
    """Get the default location for a user, if any"""
    session = get_session()
    try:
        location = session.query(SavedLocation).filter_by(
            user_id=user_id, is_default=True
        ).first()
        
        if location:
            return {
                'id': location.id,
                'name': location.name,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'is_default': location.is_default
            }
        return None
    finally:
        session.close()

def save_crop_preference(user_id, crop_name, is_favorite=True, notes=None):
    """Save a crop preference for a user"""
    session = get_session()
    
    try:
        # Check if preference already exists
        existing = session.query(CropPreference).filter_by(
            user_id=user_id, crop_name=crop_name
        ).first()
        
        if existing:
            existing.is_favorite = is_favorite
            existing.notes = notes
        else:
            preference = CropPreference(
                user_id=user_id,
                crop_name=crop_name,
                is_favorite=is_favorite,
                notes=notes
            )
            session.add(preference)
        
        session.commit()
        return True
    finally:
        session.close()

def get_crop_preferences(user_id):
    """Get all crop preferences for a user"""
    session = get_session()
    try:
        preferences = session.query(CropPreference).filter_by(user_id=user_id).all()
        # Convert to list of dictionaries to avoid session issues
        return [
            {
                'id': pref.id,
                'crop_name': pref.crop_name,
                'is_favorite': pref.is_favorite,
                'notes': pref.notes
            } 
            for pref in preferences
        ]
    finally:
        session.close()

def record_weather(latitude, longitude, location_name, temperature, humidity, rainfall=None, description=None):
    """Record weather data for historical analysis"""
    session = get_session()
    try:
        record = WeatherRecord(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,
            description=description
        )
        session.add(record)
        session.commit()
        return {
            'id': record.id,
            'latitude': record.latitude,
            'longitude': record.longitude,
            'temperature': record.temperature,
            'humidity': record.humidity
        }
    finally:
        session.close()

def get_weather_history(latitude, longitude, days=30):
    """Get weather history for a location"""
    session = get_session()
    try:
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # Find records within 0.01 degree radius (approx 1km)
        lat_min, lat_max = latitude - 0.01, latitude + 0.01
        lon_min, lon_max = longitude - 0.01, longitude + 0.01
        
        records = session.query(WeatherRecord).filter(
            WeatherRecord.latitude.between(lat_min, lat_max),
            WeatherRecord.longitude.between(lon_min, lon_max),
            WeatherRecord.recorded_at >= cutoff_date
        ).order_by(WeatherRecord.recorded_at.desc()).all()
        
        # Convert to list of dictionaries to avoid session issues
        return [
            {
                'id': rec.id,
                'recorded_at': rec.recorded_at,
                'latitude': rec.latitude,
                'longitude': rec.longitude,
                'location_name': rec.location_name,
                'temperature': rec.temperature,
                'humidity': rec.humidity,
                'rainfall': rec.rainfall,
                'description': rec.description
            } 
            for rec in records
        ]
    finally:
        session.close()

# Soil moisture sensor functions
def register_soil_moisture_sensor(user_id, name, sensor_id, location_name, latitude, longitude, 
                                field_area=None, depth=None, sensor_type=None):
    """Register a new soil moisture sensor for a user"""
    session = get_session()
    
    try:
        # Check if sensor_id already exists
        existing = session.query(SoilMoistureSensor).filter_by(sensor_id=sensor_id).first()
        if existing:
            return None  # Sensor ID must be unique
        
        sensor = SoilMoistureSensor(
            user_id=user_id,
            name=name,
            sensor_id=sensor_id,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            field_area=field_area,
            depth=depth,
            sensor_type=sensor_type,
            is_active=True
        )
        session.add(sensor)
        session.commit()
        
        # Create a dictionary with the sensor data to return
        sensor_data = {
            'id': sensor.id,
            'name': sensor.name,
            'sensor_id': sensor.sensor_id,
            'location_name': sensor.location_name,
            'latitude': sensor.latitude,
            'longitude': sensor.longitude,
            'field_area': sensor.field_area,
            'depth': sensor.depth,
            'sensor_type': sensor.sensor_type,
            'is_active': sensor.is_active
        }
        return sensor_data
    finally:
        session.close()

def get_soil_moisture_sensors(user_id):
    """Get all soil moisture sensors for a user"""
    session = get_session()
    try:
        sensors = session.query(SoilMoistureSensor).filter_by(user_id=user_id).all()
        # Convert to list of dictionaries to avoid session issues
        return [
            {
                'id': sensor.id,
                'name': sensor.name,
                'sensor_id': sensor.sensor_id,
                'location_name': sensor.location_name,
                'latitude': sensor.latitude,
                'longitude': sensor.longitude,
                'field_area': sensor.field_area,
                'depth': sensor.depth,
                'sensor_type': sensor.sensor_type,
                'is_active': sensor.is_active
            } 
            for sensor in sensors
        ]
    finally:
        session.close()

def get_soil_moisture_sensor(sensor_id):
    """Get a soil moisture sensor by ID"""
    session = get_session()
    try:
        sensor = session.query(SoilMoistureSensor).filter_by(id=sensor_id).first()
        if sensor:
            return {
                'id': sensor.id,
                'name': sensor.name,
                'sensor_id': sensor.sensor_id,
                'location_name': sensor.location_name,
                'latitude': sensor.latitude,
                'longitude': sensor.longitude,
                'field_area': sensor.field_area,
                'depth': sensor.depth,
                'sensor_type': sensor.sensor_type,
                'is_active': sensor.is_active
            }
        return None
    finally:
        session.close()

def update_soil_moisture_sensor(sensor_id, **kwargs):
    """Update a soil moisture sensor"""
    session = get_session()
    try:
        sensor = session.query(SoilMoistureSensor).filter_by(id=sensor_id).first()
        if not sensor:
            return False
        
        # Update specified fields
        for key, value in kwargs.items():
            if hasattr(sensor, key):
                setattr(sensor, key, value)
        
        session.commit()
        return True
    finally:
        session.close()

def delete_soil_moisture_sensor(sensor_id):
    """Delete a soil moisture sensor"""
    session = get_session()
    try:
        sensor = session.query(SoilMoistureSensor).filter_by(id=sensor_id).first()
        if not sensor:
            return False
        
        session.delete(sensor)
        session.commit()
        return True
    finally:
        session.close()

def record_soil_moisture_reading(sensor_id, moisture_percentage, temperature=None, 
                               electrical_conductivity=None, battery_level=None, signal_strength=None):
    """Record a new reading from a soil moisture sensor"""
    session = get_session()
    try:
        # Verify sensor exists
        sensor = session.query(SoilMoistureSensor).filter_by(id=sensor_id).first()
        if not sensor:
            return None
        
        reading = SoilMoistureReading(
            sensor_id=sensor_id,
            moisture_percentage=moisture_percentage,
            temperature=temperature,
            electrical_conductivity=electrical_conductivity,
            battery_level=battery_level,
            signal_strength=signal_strength
        )
        session.add(reading)
        session.commit()
        
        return {
            'id': reading.id,
            'recorded_at': reading.recorded_at,
            'sensor_id': reading.sensor_id,
            'moisture_percentage': reading.moisture_percentage,
            'temperature': reading.temperature,
            'electrical_conductivity': reading.electrical_conductivity,
            'battery_level': reading.battery_level,
            'signal_strength': reading.signal_strength
        }
    finally:
        session.close()

def get_soil_moisture_readings(sensor_id, days=7):
    """Get soil moisture readings for a sensor over a specified time period"""
    session = get_session()
    try:
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        readings = session.query(SoilMoistureReading).filter(
            SoilMoistureReading.sensor_id == sensor_id,
            SoilMoistureReading.recorded_at >= cutoff_date
        ).order_by(SoilMoistureReading.recorded_at.asc()).all()
        
        # Convert to list of dictionaries to avoid session issues
        return [
            {
                'id': reading.id,
                'recorded_at': reading.recorded_at,
                'sensor_id': reading.sensor_id,
                'moisture_percentage': reading.moisture_percentage,
                'temperature': reading.temperature,
                'electrical_conductivity': reading.electrical_conductivity,
                'battery_level': reading.battery_level,
                'signal_strength': reading.signal_strength
            } 
            for reading in readings
        ]
    finally:
        session.close()

# Initialize database on import
init_db()