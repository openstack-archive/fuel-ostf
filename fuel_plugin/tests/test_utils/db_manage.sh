export PGPASSWORD='ostf'
psql -U postgres -h localhost -c "drop user adapter"
psql -U postgres -h localhost -c "create role adapter with nosuperuser createdb password 'demo' login"
psql -U postgres -h localhost -c "drop database if exists testing_adapter"
psql -U postgres -h localhost -c "create database testing_adapter"