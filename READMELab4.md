# Laboratory Work #4 - Terraform + Ansible IaC

## Мета

Автоматизувати розгортання інфраструктури та конфігурації mywebapp за допомогою Terraform (VM у libvirt) та Ansible (ролі для бази, застосунку та nginx).

## Архітектура

- `db` (PostgreSQL)
- `app` (Flask застосунок)
- `nginx` (reverse proxy)

Мережа: `192.168.56.0/24`

## Структура каталогу

- `terraform/` - мережа, VM, cloud-init
- `ansible/` - inventory, group_vars, playbooks, roles

Ролі Ansible:

- `common` - базові пакети та UFW
- `users` - користувачі student/teacher/operator
- `db` - PostgreSQL
- `app` - застосунок, systemd, конфігурація
- `nginx` - reverse proxy

## Важливі змінні

Оновіть у `ansible/group_vars/all.yml`:

- `app_repo` - URL вашого репозиторію
- `student_password_hash`, `teacher_password_hash`, `operator_password_hash` - SHA-512 хеші
- `db_host`, `app_backend_host`, `nginx_host` - IP адреси VM

## Запуск

1) Terraform

```bash
cd terraform
terraform init
terraform apply
```

2) Ansible

```bash
cd ansible
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

## Перевірка

```bash
curl http://192.168.56.12/
curl http://192.168.56.12/items
```

## Примітки

- Cloud-init додає ключ у користувача `student`.
- UFW відкриває лише потрібні порти.
- Якщо змінили IP адреси у Terraform, оновіть `inventory/hosts.ini` та `group_vars/all.yml`.
