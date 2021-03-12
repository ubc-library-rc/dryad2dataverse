SELECT count (lastName|', '|firstName) AS AuthCount, 
lastName||', ' ||firstname as author,
affiliation
FROM authors 
WHERE affiliation LIKE '%British Columbia%'
GROUP BY author, affiliation
ORDER BY AuthCount DESC ;