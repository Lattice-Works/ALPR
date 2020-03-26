# This creates a copy of the recurring atlas table (overwritten every 10 min)
# that is identical to original recurring table except for 1 thing:
# We save readStamp as "timestamp with timezone" instead of its original "timestamp without tiemzone"
# Otherwise was integrating '12:00 UTC' as '12:00 PST'

from sqlalchemy.types import Integer, String, Float, TIMESTAMP, Binary
import sqlalchemy as db
import pandas as pd
import argparse
import yaml


# INPUT ARGUMENTS
def get_parser():
    parser = argparse.ArgumentParser(description='QA check on aggregate launchpad pulls. Compare to count from source.')
    parser.add_argument('--config', required=True)
    parser.add_argument('--datasource', required=True)
    parser.add_argument('--recur_table', required=True)

    args = parser.parse_args()
    return args



##
####
######
######## CONVERT & COPY TABLE ###########
def main():
    # Connect to db
    args = get_parser()  # get the args from the parser function
    with open(args.config, 'r') as fl:
        # with open(config, 'r') as fl:
        configfile = yaml.load(fl, Loader=yaml.FullLoader)

    db_user = configfile['hikariConfigs'][args.datasource]['username']
    db_pwd = configfile['hikariConfigs'][args.datasource]['password']
    jdbcUrl = configfile['hikariConfigs'][args.datasource]['jdbcUrl']
    db_name = jdbcUrl.split("/")[::-1][0].split("?")[0]
    atlastable = args.recur_table

    engine = db.create_engine(f'postgresql://{db_user}:{db_pwd}@atlas.openlattice.com:30001/{db_name}',
                              connect_args={'sslmode': 'require'})

   # Get table from atlas
    atlas_query = "select * from {table};".format(
        table=atlastable
    )
    atlas_df = pd.read_sql_query(atlas_query, engine)

    # Copy table
    clean_atlas = atlas_df

    # Set dates & datetimes in cleaned table - THE KEY STEP
    clean_atlas ['readStamp'] = clean_atlas ['readStamp'].dt.tz_localize("UTC")

    # Now copy cleaned table back into atlas and overwrite itself
    # Identical to original recurring table except readStamp = "timestamp with timezone"
    clean_atlas.to_sql('zzz_recurring_clean', con=engine, index=False, if_exists='replace',
                       dtype={'id': Integer,
                              'readstamp': TIMESTAMP(timezone=True),
                              'plate': String,
                              'latitude': Float,
                              'longitude': Float,
                              'image1': Binary,
                              'image2': Binary,
                              'agency': String,
                              'camera_description': String,
                              'company_id': Integer,
                              'camera_id': Integer,
                              'site_id': Integer
                              })

    if __name__ == '__main__':
        main()


