db.createUser(
    {
        user: "cpg_user",
        pwd: "read_manual",
        roles: [ { role: "readWrite", db: "cpg" } ]
    }
)
