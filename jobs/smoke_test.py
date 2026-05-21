from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("MarketStreamSmokeTest")
    .master("local[*]")
    .getOrCreate()
)

print("Spark version:", spark.version)

df = spark.createDataFrame(
    [("AAPL", 195.0), ("MSFT", 410.0), ("GOOG", 175.0)],
    ["ticker", "price"],
)
df.show()
print("Row count:", df.count())

spark.stop()
print("Smoke test passed.")