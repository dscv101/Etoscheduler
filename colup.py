# This script is designed to run in Power BI's Power Query Editor
# It converts datetime values to duration format (hh:mm:ss)

import datetime

def transform_column(dataset):
    # Make a copy to avoid modifying the original dataset
    output_dataset = dataset.copy()
    
    try:
        # Get the first datetime column in the dataset
        datetime_cols = [col for col in output_dataset.columns 
                        if output_dataset[col].dtype in ['datetime64[ns]', 'object']]
        
        if not datetime_cols:
            raise ValueError("No datetime columns found in the dataset")
        
        target_col = datetime_cols[0]
        
        # Convert datetime objects to duration format
        def to_duration(dt):
            try:
                if isinstance(dt, str):
                    dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
                
                # Extract hours, minutes, and seconds
                total_seconds = dt.hour * 3600 + dt.minute * 60 + dt.second
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                # Format as hh:mm:ss
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            except Exception as e:
                return None
        
        # Apply the transformation
        output_dataset[f"{target_col}_duration"] = output_dataset[target_col].apply(to_duration)
        
        return output_dataset
    
    except Exception as e:
        print(f"Error processing dataset: {str(e)}")
        return dataset

# Example usage in Power BI Power Query:
# dataset = transform_column(dataset)