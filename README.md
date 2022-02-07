# monte-carlo-crypto-data

## Usage:

### Get All Metric Names:
https://sz1j1xggd7.execute-api.us-east-1.amazonaws.com/v1/metrics

### Get Single Metric Day Timeseries
https://sz1j1xggd7.execute-api.us-east-1.amazonaws.com/v1/metric/{metric-name}/timeseries

eg. https://sz1j1xggd7.execute-api.us-east-1.amazonaws.com/v1/metric/hottry/timeseries

### Get Single Metric Rank
https://sz1j1xggd7.execute-api.us-east-1.amazonaws.com/v1/metric/{metric-name}/rank

eg. https://sz1j1xggd7.execute-api.us-east-1.amazonaws.com/v1/metric/hottry/rank

## Architecture: 
This is deployed in my AWS account. The Code here is for the 4 lambda functions that comprise this.

### Ingest:
There is a lambda for the ingest side. This lambda queries the cryptwatch prices endpoint every minute to gather 
all of the prices for each symbol in the crypto markets. Then we convert the api response into a parquet file and
push it into S3.

### Database:
There is a single table sitting on top of the S3 bucket where we store our ingested data
We are using Amazon Athena as our query engine to grab data out of that bucket

### API:
There is a lambda function powering each of the 3 endpoints we support. Those lambdas query the database on demand.

## Enhancements:

### Deployment:
Right now, everything is basically handrolled in AWS without much reproducability. One of the first things to improve is to define everything in a CloudFormation Template and deploy the whole package through the cli.

### Authentication:
Currently Everything is open to the world (I will be shutting this down soon after its discussed)

### API Data Format:
While its clear what each row is, there is a lot of repeated information (the repeated keys), I would prefer a data format that contains metadata once, instead of repeating it with every row. For this exercise, I felt clarity was a bit more important.




## Scaling:
There are a lot of ways we could improve scale. 

### Ingest
On the Ingest side, we currently expect to grab all metrics, convert them to parquet
and upload them in a single minute. If there are a lot more metrics we need to ingest, we might consider partitioning our ingests - we may
be able to break down the api request->datalake input loop by market, or by some hash of metrics. If we need to ingest at a higher rate, our architcture here may not scale - I'd recommend moving to stream processing type archicture instead of a poll (assuming we can receive a stream of data) as well as moving the database layer over to a timeseries database. The key there is that we can focus on processing on the record level, instead of processing a whole batch at once.

### API
On the API side, if there are a lot of users requesting the apis we can do a number of things. If we're still using athena, we can increase the number of workgroups we're using so fewer users are on a single one. We can also add a caching layer for the most common requests so we don't have to go back to the database for every query. We could also add paging to the api so that we are returning/querying less data with every request.

## Testing:
Outside of standard unit testing, and a set of smoke tests around the apis ensuring that they are reachable, and return data with the right formats - the main set of tests I would focus on would be tests around the database layer. Especially because some of the queries we have are complex (ahem, rank), I would want to ensure that those queries are done correctly. I would inject a small test database with known outcomes for distinct names, timeseries, and rank, and write an automatic integration test that runs the associated queries and ensures we get the expected results.

## Feature Request:
Send users alerts whenever a metric is 3X its average value for the last hour.
	
### Proposal:
This feature basically breaks down into 2 pieces of functionality - saving user notification information, and detecting
the 3x jump. Saving user information involves adding a table with that information, and we can receive that through some form, or api. The 'Jump Detection' could be implemented as such: Imagining we are using the architecture we have here, when the ingest lambda is finished, it can push an event. We can listen for that event in a 'Jump Detection Lambda'. We have a query that the jump detection lambda runs in the database that will find all metrics that meet the criteria (i.e. Select metric, value where value > 3*(avg_value over last hour)). That lambda can read from the user notification table, and notify all users of those metrics. If we're using a streaming approach, we could build 60 minute sliding windows for each metric, and send events out when metrics meet the criteria, then, we can have a listener on the other side which can take those messages in and do the notifications.
