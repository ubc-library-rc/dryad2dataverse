SELECT round(sum(sizeMb),2) as 'Total MB',
round(sum(sizeMb)/1024,2) as 'Total GB'
FROM size;