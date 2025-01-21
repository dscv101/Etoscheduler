from __future__ import annotations

# Optimize imports by grouping and ordering
# Standard library
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple

# Third-party libraries
import numpy as np
import pandas as pd
import yaml
from sklearn.impute import KNNImputer

@dataclass(frozen=True)
class DataQualityReport:
    """Immutable data structure for holding data quality metrics"""
    total_rows: int
    duplicate_count: int
    missing_counts: Dict[str, int]
    stats: Dict[str, Dict[str, float]]
    outliers: Dict[str, int]
    quality_score: float

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> DataQualityReport:
        """Factory method to create report from DataFrame"""
        stats = {
            column: {
                'mean': df[column].mean() if pd.api.types.is_numeric_dtype(df[column]) else None,
                'std': df[column].std() if pd.api.types.is_numeric_dtype(df[column]) else None,
                'unique': df[column].nunique()
            }
            for column in df.columns
        }
        
        outliers = {
            column: np.sum(np.abs(stats) > 3)
            for column, stats in (
                (col, (df[col] - df[col].mean()) / df[col].std())
                for col in df.select_dtypes(include=['number']).columns
            )
        }
        
        quality_score = (
            (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) +
            (1 - len(df[df.duplicated()]) / len(df)) +
            (1 - sum(outliers.values()) / (len(df) * len(outliers) or 1))
        ) / 3
        
        return cls(
            total_rows=len(df),
            duplicate_count=len(df[df.duplicated()]),
            missing_counts=df.isnull().sum().to_dict(),
            stats=stats,
            outliers=outliers,
            quality_score=quality_score
        )

class DataValidator:
    """Handles data validation with functional approach"""
    
    def __init__(self, schema_path: Optional[str] = None):
        self.schema = self._load_schema(schema_path) if schema_path else {}
    
    @staticmethod
    def _load_schema(schema_path: str) -> Dict:
        """Load schema using context manager"""
        with open(schema_path) as f:
            return yaml.safe_load(f)
    
    def validate_dataframe(self, df: pd.DataFrame) -> List[str]:
        """Validate DataFrame using list comprehension and generators"""
        if not self.schema:
            return []
        
        return [
            violation
            for column, rules in self.schema.get('columns', {}).items()
            for violation in self._check_column_rules(df, column, rules)
        ]
    
    def _check_column_rules(self, df: pd.DataFrame, column: str, rules: Dict) -> Generator[str, None, None]:
        """Generator for validation rules"""
        if column not in df.columns:
            yield f"Missing required column: {column}"
            return
        
        if expected_type := rules.get('type'):
            if not df[column].dtype.name.startswith(expected_type):
                yield f"Column {column} has incorrect type"
        
        if (min_val := rules.get('min')) is not None and df[column].min() < min_val:
            yield f"Column {column} contains values below minimum"
        
        if (max_val := rules.get('max')) is not None and df[column].max() > max_val:
            yield f"Column {column} contains values above maximum"

class ETLPipeline:
    """ETL pipeline with optimized processing"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.input_path = Path(self.config['input_path'])
        self.output_path = Path(self.config['output_path'])
        self.validator = DataValidator(self.config.get('schema_path'))
        self._setup_logging()
    
    @staticmethod
    def _load_config(config_path: str) -> Dict:
        """Load configuration using context manager"""
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> None:
        """Configure logging with dict configuration"""
        log_config = self.config.get('logging', {})
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_config.get('file', 'etl.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _read_json_chunks(self, chunk_size: int = 1000) -> Generator[List[Dict], None, None]:
        """Generator for reading large JSON files in chunks"""
        with open(self.input_path) as f:
            data = json.load(f)
            for i in range(0, len(data), chunk_size):
                yield data[i:i + chunk_size]
    
    def extract(self) -> Iterator[pd.DataFrame]:
        """Extract data using generators"""
        try:
            self.logger.info(f"Starting extraction from {self.input_path}")
            return (
                pd.DataFrame(chunk)
                for chunk in self._read_json_chunks()
            )
        except Exception as e:
            self.logger.error(f"Extraction error: {str(e)}")
            raise
    
    @staticmethod
    def _process_chunk(df: pd.DataFrame) -> pd.DataFrame:
        """Process a single chunk with optimized operations"""
        # Use NumPy operations instead of loops
        numeric_cols = df.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            df[numeric_cols] = df[numeric_cols].apply(
                lambda x: np.where(np.abs(x - x.mean()) > 3 * x.std(), x.median(), x)
            )
        
        # Optimize categorical processing
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            if df[col].isnull().any():
                top_val = df[col].value_counts(normalize=True).index[0]
                df[col] = df[col].fillna(top_val)
        
        return df
    
    def transform(self, chunks: Iterator[pd.DataFrame]) -> pd.DataFrame:
        """Transform data using parallel processing"""
        try:
            self.logger.info("Starting transformation")
            
            # Process chunks in parallel
            with ProcessPoolExecutor() as executor:
                processed_chunks = list(executor.map(self._process_chunk, chunks))
            
            # Combine chunks efficiently
            df = pd.concat(processed_chunks, ignore_index=True)
            
            # Generate quality report
            quality_report = DataQualityReport.from_dataframe(df)
            self.logger.info(f"Data quality score: {quality_report.quality_score:.2f}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Transformation error: {str(e)}")
            raise
    
    def load(self, df: pd.DataFrame) -> None:
        """Load data with efficient writing"""
        try:
            self.logger.info(f"Starting load to {self.output_path}")
            
            # Ensure directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use efficient CSV writing
            df.to_csv(
                self.output_path,
                index=False,
                compression='gzip' if str(self.output_path).endswith('.gz') else None
            )
            
            self.logger.info(f"Saved {len(df)} records")
            
        except Exception as e:
            self.logger.error(f"Load error: {str(e)}")
            raise
    
    def run(self) -> None:
        """Execute pipeline with timing"""
        start_time = datetime.now()
        
        try:
            # Use generator pipeline
            data_chunks = self.extract()
            transformed_data = self.transform(data_chunks)
            self.load(transformed_data)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Pipeline completed in {execution_time:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            raise

def main() -> None:
    """Entry point with error handling"""
    try:
        pipeline = ETLPipeline("config/etl_config.yaml")
        pipeline.run()
    except Exception as e:
        logging.error(f"ETL process failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()