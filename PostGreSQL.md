By default you can only login as 'postgresql' system user, which can be done by many ways, one is: `$ su postgres` 
There, open postgresql console mode using `psql`

User: postgres
password: )dr8;E68sdg6  

psql password for postgres user: $pu?z#OrFnr5   
OUR DATABASE: group17_db   
group17 user password: yF2kC@ln6!9VN)    

Access postgreSQL database:
1. Change to postgres user
	`$ su postgres`
2. Open psql using: 
	`$ psql`
3. use database by flag '\c'
	`$ \c group17_db`
4.	show all tables 
	`$ \dt` 

SELECT * FROM auth_group;
SELECT * FROM auth_group_permissions;
SELECT * FROM auth_permission;
SELECT * FROM auth_user;
SELECT * FROM auth_user_groups;
SELECT * FROM auth_user_user_permissions;
SELECT * FROM django_admin_log;
SELECT * FROM django_content_type;
SELECT * FROM django_migrations;
SELECT * FROM django_session;
SELECT * FROM myapp_message;
SELECT * FROM myapp_profile;
