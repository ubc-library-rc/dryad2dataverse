SELECT size.doi, title.title, round(sizeMb,2) as sizeMb, 
round(sizeMb/1024,2) as TotalGb, 
round(sizeMb/1024/(SELECT sum(sizeMb) /1024 FROM size)*100, 2) AS percentSize
FROM size
INNER JOIN title on size.doi = title.doi
ORDER BY TotalGb DESC;