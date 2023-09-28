def merge_field_reviews(current_json, new_json):
    """
        Merge reviews from contributors and reviewers into a single JSON object.

        Args:
        current_json (dict): The current JSON object containing reviewer's reviews.
        new_json (dict): The new JSON object containing contributor's reviews.

        Returns:
        dict: The merged JSON object containing both contributor's and reviewer's reviews.

        Note:
        If the same key is present in both the contributor's and reviewer's reviews,
        the function will merge the field evaluations. Otherwise, it will create a new entry
        in the Review-Dict.
        """
    merged_json = new_json.copy()
    review_dict = {}

    for contrib_review in merged_json["reviews"]:
        category = contrib_review["category"]
        key = contrib_review["key"]
        review_dict[(category, key)] = contrib_review["fieldReview"]

    for reviewer_review in current_json["reviews"]:
        category = reviewer_review["category"]
        key = reviewer_review["key"]

        if (category, key) in review_dict:
            # Add field evaluations to the existing entry
            existing_field_review = review_dict[(category, key)]
            if isinstance(existing_field_review, dict):
                existing_field_review = [existing_field_review]
            if isinstance(reviewer_review["fieldReview"], dict):
                reviewer_review["fieldReview"] = [reviewer_review["fieldReview"]]
            merged_field_review = existing_field_review + reviewer_review["fieldReview"]
            review_dict[(category, key)] = merged_field_review
        else:
            # Create new entry in Review-Dict
            review_dict[(category, key)] = reviewer_review["fieldReview"]

    # Insert updated field scores back into the JSON
    merged_json["reviews"] = [
        {"category": category, "key": key, "fieldReview": review_dict[(category, key)]}
        for category, key in review_dict
    ]

    return merged_json

def get_review_for_key(key, review_data):
    """
        Retrieve the review for a specific key from the review data.

        Args:
        key (str): The key for which to retrieve the review.
        review_data (dict): The review data containing reviews for various keys.

        Returns:
        Any: The new value associated with the specified key in the review data, or None if the key is not found.
        """

    for review in review_data["reviewData"]["reviews"]:
        if review["key"] == key:
            return review["fieldReview"].get("newValue", None)
    return None

def recursive_update(metadata, review_data):
    """
        Recursively update the metadata with new values from the review data.

        Args:
        metadata (dict): The original metadata dictionary to be updated.
        review_data (dict): The review data containing new values for various keys.

        Note:
        The function traverses the review data, and for each key, it updates the corresponding
        value in the metadata if a new value is present and is not an empty string.
        """

    for review_key in review_data["reviewData"]["reviews"]:
        keys = review_key["key"].split('.')

        if isinstance(review_key["fieldReview"], list):
            for field_review in review_key["fieldReview"]:
                new_value = field_review.get("newValue", None)
                if new_value is not None and new_value != "":
                    set_nested_value(metadata, keys, new_value)
        else:
            new_value = review_key["fieldReview"].get("newValue", None)
            if new_value is not None and new_value != "":
                set_nested_value(metadata, keys, new_value)

def set_nested_value(metadata, keys, value):
    """
        Set a nested value in a dictionary given a sequence of keys.

        Args:
        metadata (dict): The dictionary in which to set the value.
        keys (list): A list of keys representing the path to the nested value.
        value (Any): The value to set.

        Note:
        The function navigates through the dictionary using the keys and sets the value
        at the position indicated by the last key in the list.
        """

    for key in keys[:-1]:
        if key.isdigit():
            key = int(key)
        metadata = metadata[key]
    last_key = keys[-1]
    if last_key.isdigit():
        last_key = int(last_key)
    metadata[last_key] = value


def process_review_data(review_data, metadata, categories):
    """
        Process the review data and update the metadata with the latest reviews and suggestions.

        Args:
        review_data (list): A list of dictionaries containing review data for each field.
        metadata (dict): The original metadata object that needs to be updated.
        categories (list): A list of categories in the metadata.

        Returns:
        dict: A state dictionary containing the state of each field after processing the review data.

        Note:
        The function sorts the fieldReview entries by timestamp (newest first) and updates the metadata
        with the latest reviewer suggestions, comments, and new values. The resulting state dictionary
        indicates the state of each field after processing.
        """
    state_dict = {}

    for review in review_data:
        field_key = review.get("key")
        field_review = review.get("fieldReview")

        if isinstance(field_review, list):
            # Sortiere die fieldReview-Einträge nach dem timestamp (neueste zuerst)
            sorted_field_review = sorted(
                field_review, key=lambda x: x.get("timestamp"), reverse=True
            )
            latest_field_review = (
                sorted_field_review[0] if sorted_field_review else None
            )

            if latest_field_review:
                state = latest_field_review.get("state")
                reviewer_suggestion = latest_field_review.get("reviewerSuggestion")
                reviewer_suggestion_comment = latest_field_review.get("comment")
                newValue = latest_field_review.get("newValue")
            else:
                state = None
                reviewer_suggestion = None
                reviewer_suggestion_comment = None
                newValue = None
        else:
            state = field_review.get("state")
            reviewer_suggestion = field_review.get("reviewerSuggestion")
            reviewer_suggestion_comment = field_review.get("comment")
            newValue = field_review.get("newValue")

        if reviewer_suggestion is not None and reviewer_suggestion_comment is not None:
            for category in categories:
                for item in metadata[category]:
                    if item["field"] == field_key:
                        item["reviewer_suggestion"] = reviewer_suggestion
                        item["suggestion_comment"] = reviewer_suggestion_comment
                        break

        if newValue is not None:
            for category in categories:
                for item in metadata[category]:
                    if item['field'] == field_key:
                        item['newValue'] = newValue
                        break

        state_dict[field_key] = state

    return state_dict

