const path = require('path')
const { config } = require("dotenv")
const { toGraphQLTypeDefs } = require("@neo4j/introspector")
const neo4j = require("neo4j-driver");
const fs = require('fs');

config()

const driver = neo4j.driver(
    process.env.NEO4J_URI!,
    neo4j.auth.basic(process.env.NEO4J_USER!, process.env.NEO4J_PASSWORD!)
  );

const sessionFactory = () => driver.session({ defaultAccessMode: neo4j.session.READ, database: "neo4j" })

// We create a async function here until "top level await" has landed
// so we can use async/await
async function main() {
    const typeDefs = await toGraphQLTypeDefs(sessionFactory)
    fs.writeFileSync( path.join(__dirname, 'schema.graphql'), typeDefs)
    await driver.close();
}
main()
