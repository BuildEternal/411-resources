#!/bin/bash

# Define the base URL for the Flask boxing API
BASE_URL="http://localhost:5001/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection and table
check_db() {
  echo "Checking database connection and boxers table..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Database and boxers table are healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

###############################################
#
# Boxer Management
#
###############################################

add_boxer() {
  name="$1"
  weight="$2"
  height="$3"
  reach="$4"
  age="$5"

  echo "Adding boxer: $name..."
  curl -s -X POST "$BASE_URL/add-boxer" -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\", \"weight\":$weight, \"height\":$height, \"reach\":$reach, \"age\":$age}" \
    | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Boxer '$name' added successfully."
  else
    echo "Failed to add boxer '$name'."
    exit 1
  fi
}

delete_boxer() {
  boxer_id="$1"

  echo "Deleting boxer with ID ($boxer_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-boxer/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer deleted successfully with ID ($boxer_id)."
  else
    echo "Failed to delete boxer with ID ($boxer_id)."
    exit 1
  fi
}

get_boxer_by_id() {
  boxer_id="$1"

  echo "Retrieving boxer by ID ($boxer_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-id/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by ID ($boxer_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON (ID $boxer_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve boxer by ID ($boxer_id)."
    exit 1
  fi
}

get_boxer_by_name() {
  boxer_name="$1"
  encoded_name=$(echo "$boxer_name" | sed 's/ /%20/g')

  echo "Retrieving boxer by name ($boxer_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-name/$encoded_name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by name ($boxer_name)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON (Name: $boxer_name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve boxer by name ($boxer_name)."
    exit 1
  fi
}

###############################################
#
# Ring and Fight Management
#
###############################################

clear_boxers() {
  echo "Clearing all boxers from ring..."
  response=$(curl -s -X POST "$BASE_URL/clear-boxers")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxers cleared from ring successfully."
  else
    echo "Failed to clear boxers from ring."
    exit 1
  fi
}

enter_ring() {
  boxer_name="$1"
  echo "Entering boxer '$boxer_name' into the ring..."
  response=$(curl -s -X POST "$BASE_URL/enter-ring" -H "Content-Type: application/json" \
    -d "{\"name\": \"$boxer_name\"}")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer '$boxer_name' entered the ring successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Ring JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to enter boxer '$boxer_name' into the ring."
    exit 1
  fi
}

get_boxers() {
  echo "Retrieving list of boxers in the ring..."
  response=$(curl -s -X GET "$BASE_URL/get-boxers")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxers in the ring retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxers JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve boxers from the ring."
    exit 1
  fi
}

fight() {
  echo "Triggering a fight..."
  response=$(curl -s -X GET "$BASE_URL/fight")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Fight complete. Winner details:"
    if [ "$ECHO_JSON" = true ]; then
      echo "$response" | jq .
    else
      echo "$response" | grep '"winner":'
    fi
  else
    echo "Fight failed to execute."
    exit 1
  fi
}

get_leaderboard() {
  echo "Retrieving leaderboard sorted by wins..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=wins")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve leaderboard."
    exit 1
  fi
}

###############################################
#
# Run tests sequentially
#
###############################################

# Health and DB checks
check_health
check_db

# Clear boxers from ring (and optionally clear existing boxers from DB if supported)
clear_boxers

# Add boxers
add_boxer "Mike Tyson" 150 178 71.0 30
add_boxer "Muhammad Ali" 125 183 78.0 30

# Retrieve boxers to ensure they were added
get_boxer_by_id 1
get_boxer_by_name "Muhammad Ali"

# Enter boxers into the ring
enter_ring "Mike Tyson"
enter_ring "Muhammad Ali"

# Get list of boxers in the ring
get_boxers

# Trigger a fight (requires two boxers in the ring)
fight

# Retrieve leaderboard
get_leaderboard

# Delete a boxer (delete boxer with ID 1)
delete_boxer 1

# Attempt to retrieve deleted boxer (this should fail)
echo "Verifying deletion of boxer with ID 1..."
response=$(curl -s -X GET "$BASE_URL/get-boxer-by-id/1")
if echo "$response" | grep -q '"status": "error"'; then
  echo "Boxer deletion confirmed (boxer with ID 1 not found)."
else
  echo "Boxer with ID 1 still exists. Deletion test failed."
  exit 1
fi

echo "All tests passed successfully!"
