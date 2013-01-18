server {
	listen 80;
        server_name example.com *.example.com;

	root /srv/www/example;
	index index.html index.htm;
}
