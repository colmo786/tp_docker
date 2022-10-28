select case 
	when actual_ts is not null then actual_ts
	else future_ts
	end as ts
	, hourly_demand
	, hourly_demand_forecast
from
(
	select A.timestamp as actual_ts
		, A.hourly_demand
		, F.timestamp as future_ts
		, F.hourly_demand_forecast from cammesa_db.hourly_demand A
	full outer join cammesa_db.hourly_demand_forecast F on F.timestamp = A.timestamp
) as subquery
where actual_ts >= '2022-10-02' and actual_ts < '2022-10-03'
order by actual_ts, future_ts