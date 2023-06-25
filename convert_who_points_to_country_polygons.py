import arcpy


def convert_who_points_to_country_polygons(input_data, countries_layer, date_field):
    """This function takes an input point layer of WHO Covid-19 daily reporting data and converts the points to
    polygons. The result is a polygon layer of daily reported Covid-19 data for each country which can be symbolized
    in GIS software using graduated colors and combined with a time series widget to display Covid-19 case data
    over time."""

    # set environment to overwrite outputs
    arcpy.env.overwriteOutput = True
    # Set the workspace environment
    arcpy.env.workspace = r"C:\Users\bfure\Documents\School\PennState\Masters\GEOG597G\Data\ArcGISPro\GeoRelief.gdb"
    # create empty list to store dates
    date_list = []
    # Create an empty list to store the feature class paths
    polygon_fc_list = []
    # Create an empty list to store the feature class paths
    fc_path_list = []
    # set counters to keep track of point and polygon layers created for output layer naming purposes
    point_layer_counter = 1
    polygon_layer_counter = 1

    # create list of dates in input WHO data
    with arcpy.da.SearchCursor(input_data, [date_field]) as date_cursor:
        for row in date_cursor:
            date = row[0].strftime("%m/%d/%Y")
            if date not in date_list:
                date_list.append(date)
    # clean up cursor
    del row, date_cursor

    # For each day in the WHO data, select all records with that date, join those records to the country polygons,
    # and export as a layer, so that each layer contains all the records of data for one particular date
    # Then take each layer and aggregate into one polygon layer

    # loop through each date in the  date list
    for reported_date in date_list:
        # define where clause for attribute selection
        where_clause = f"{arcpy.AddFieldDelimiters(input_data, date_field)} = date '{reported_date}'"
        # create selection layer of records for the current data
        selection_layer = arcpy.management.SelectLayerByAttribute(input_data, "NEW_SELECTION", where_clause, "")
        # define an output point layer name
        output_point_layer_name = f"Output_Point_Layer_{point_layer_counter}"
        # increase point layer counter by one for output name purposes
        point_layer_counter += 1
        # create output point layer of records from current date
        arcpy.management.CopyFeatures(selection_layer, output_point_layer_name, "", "", "", "")
        # join current date point layer to country polygons layer
        joined_layer = arcpy.management.AddJoin(countries_layer, "ISO", output_point_layer_name, "Country_code", "KEEP_COMMON", "")
        # define an output point layer name
        output_polygon_layer_name = f"Output_Polygon_Layer_{polygon_layer_counter}"
        # create output polygon layer of records from current date
        arcpy.management.CopyFeatures(joined_layer, output_polygon_layer_name, "", "", "", "")
        # append the current polygon layer name to the list to create a list of feature classes to append together later
        polygon_fc_list.append(output_polygon_layer_name)
        # increase polygon layer counter by one for output name purposes
        polygon_layer_counter += 1
        # remove the join from the countries layer to reset for the next row
        arcpy.management.RemoveJoin(countries_layer, "")

    # when exporting features from a join, the field names are modified to include the name of the join layer, so in
    # order to correctly handling appending the layers together later, the field names in each output polygon layer
    # need to be updated to their original field name

    # iterate through polygon layers
    for x in range(1, len(polygon_fc_list) + 1):
        # define search text for the field name
        field_name_search_text = f"Output_Point_Layer_{x}_"

        # Iterate over each feature class
        for feature_class in polygon_fc_list:
            # Get the list of existing fields in the feature class
            fields = arcpy.ListFields(feature_class)
            # Create a dictionary to store the old and new field names
            field_mapping = {}

            # Loop through the fields
            for field in fields:
                # define variable to store field name
                old_name = field.name

                # don't rename OBJECTID field as there is another OBJECTID field already and this field isn't needed
                if "OBJECTID" in old_name:
                    continue

                # if the matching search text is in the field name
                if field_name_search_text in old_name:
                    # set the new name to the original field name by replacing the search text with empty string
                    new_name = old_name.replace(field_name_search_text, "")

                    # field names are limited to 31 characters or less in this context (normally 64)
                    if len(new_name) < 31:
                        # if new field name is less than 31 characters, add new name to dictionary
                        field_mapping[old_name] = new_name

            # Check out the data editing session
            arcpy.CheckOutExtension("DataManagement")

            # Use the AlterField tool to rename the fields
            for old_name, new_name in field_mapping.items():
                arcpy.AlterField_management(feature_class, old_name, new_name, new_name)

            # Check in the data editing session
            arcpy.CheckInExtension("DataManagement")

    # remove the first polygon layer from the polygon_fc_list since all other polygons will be appended to this one.
    # so it doesn't need to be included in list
    polygon_fc_list.remove("Output_Polygon_Layer_1")

    # Loop through the feature classes and get their full paths
    for fc in polygon_fc_list:
        fc_path = arcpy.env.workspace + "\\" + fc
        fc_path_list.append(fc_path)

    # append each output polygon layer (of which each represents a single date's worth of reported data) to the
    # first polygon layer to create a merged dataset
    arcpy.management.Append(fc_path_list, "Output_Polygon_Layer_1", "NO_TEST", "", "", "", "", "")


# define input parameters
input_data = "WHO_Geocode_May_June_2023_NEW"
countries_layer = "World_Countries"
date_field = "Date_reported"

# call function to convert WHO data points to country polygons
convert_who_points_to_country_polygons(input_data, countries_layer, date_field)
