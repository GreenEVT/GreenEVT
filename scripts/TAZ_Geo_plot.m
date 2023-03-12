%% TAZ Overload Plotting Script

% Reuires the MappingToolbox to extend the features of geoplot
clear

% Make the script work on Windows, Linux, and Mac

if ispc
    fileslash = '\';
else
    fileslash = '/';
end


[bus_data, taz_data, substation_data, repo_dir] = readData(fileslash);
[overload_files] = find_overload_files(repo_dir);


line_overloads = [];
transformer_overloads = [];
other_components_overloads = [];
% Determine Overloads at each Interval
for i = 1:height(overload_files)
    disp(['Computing Interval File ', num2str(i), ' out of ', num2str(height(overload_files))])

    filename = overload_files.Filename{i};
    interval = overload_files.Interval(i);
           
    overload_data = readcell([repo_dir fileslash 'test' fileslash 'open_dss' fileslash filename]);
    if i == 1
        [bus_overloads,transformer_overloads_new,line_overloads_new,other_components_overloads_new] = find_overloaded_buses(overload_data);
        transformer_overloads = [transformer_overloads transformer_overloads_new];
        line_overloads = [line_overloads line_overloads_new];
        other_components_overloads = [other_components_overloads other_components_overloads_new];
        previous_data = overload_data;
    elseif isempty(setdiff(overload_data(:,1),previous_data(:,1))) && height(overload_data) == height(previous_data)
        % Same Overloads so same TAZ Overloads
        col_name = ['Overloads ' num2str(interval)];
        previous_TAZ_overloads = array2table(taz_data.(i+3),"VariableNames",{col_name});
        taz_data = [taz_data, previous_TAZ_overloads];
        transformer_overloads = [transformer_overloads transformer_overloads(end)];
        line_overloads = [line_overloads line_overloads(end)];
        other_components_overloads = [other_components_overloads other_components_overloads(end)];
        continue
    else
        [bus_overloads,transformer_overloads_new,line_overloads_new,other_components_overloads_new] = find_overloaded_buses(overload_data);
        transformer_overloads = [transformer_overloads transformer_overloads_new];
        line_overloads = [line_overloads line_overloads_new];
        other_components_overloads = [other_components_overloads other_components_overloads_new];
        previous_data = overload_data;
    end
    [taz_data] = find_taz_overloads(bus_overloads,bus_data,substation_data,taz_data,interval);

end
%}

%count and plot the overloads per interval
interval_overloads = zeros(size(overload_files,1),1);
for i = 1:length(interval_overloads)
    col = "Overloads "+num2str(overload_files.Interval(i));
    interval_overloads(i) = sum(taz_data.(col));
end
figure('Name','Overloads per interval');
plot(overload_files.Interval,interval_overloads)
hold on
plot(overload_files.Interval,transformer_overloads)
plot(overload_files.Interval,line_overloads)
plot(overload_files.Interval,other_components_overloads)
legend('Total','Transformers','Lines','Other components')
ylabel('Number of Overloads')
xlabel('Interval')
hold off



% Set up Geoplot
f = figure(2);
gx = geoaxes("Parent",f,'position',[0.13 0.19  0.77 0.74],"Basemap","streets-light");
latitude = 36.07060161;
longitude =  -79.82494956;
gx.MapCenter = [latitude, longitude];
gx.ZoomLevel = 13.5;

plotData(gx,taz_data, interval)

minInt = overload_files.Interval(1);
maxInt = overload_files.Interval(end);
minIntTxt = uicontrol('Parent',f,'Style','text','Position',[200,75,30,23],...
                'String',minInt, 'FontSize',10);
maxIntTXT = uicontrol('Parent',f,'Style','text','Position',[1300,75,30,23],...
                'String',maxInt,'FontSize',10);
hText = uicontrol( f, 'Style', 'text', 'Position', [675 40 150 30], ...
                'String', ['Interval = ' num2str(interval)],'FontSize',10 );
hSlider = uicontrol( f, 'Style', 'slider','Position', [250,75,1000,23], ...
    'Min', minInt/5, 'Max', maxInt/5, 'Value', interval/5);
hSlider.Callback =  @(src,evt) sliderCallback( src, hText, gx, taz_data) ;

%% Functions

%% Slider Function
% Updates Plot
function sliderCallback( hSlider, hText, gx, taz_data)
    idx = round( hSlider.Value )*5;
    hText.String = ['Interval = ',num2str( idx )];
    plotData(gx,taz_data,idx)
end

%% Find Overload Files
function [overload_files] = find_overload_files(repo_dir)
    myfolder = dir([repo_dir '/test/open_dss']);
    overload_files = [];
    
    for i = 1:length(myfolder)
        key_word = 'overloads_';
        if contains(myfolder(i).name,key_word)
            newfile = myfolder(i).name;
            [~,interval] = strtok(newfile,'_');
            [interval,~] = strtok(interval(2:end),'.');
            interval = str2double(interval);

            overload_files = [overload_files; {newfile}, {interval}];
        end
    end
    overload_files = cell2table(overload_files,"VariableNames",["Filename", "Interval"]);
    overload_files = sortrows(overload_files,{'Interval'},{'ascend'});
end

%% Pull Data/Info from Databases
function [bus_data, taz_data, substation_data, repo_dir] = readData(fileslash) 
    % Database Info
    current_dir = pwd;
    idxs   = strfind(current_dir, fileslash);
    repo_dir = current_dir(1:idxs(end)-1);
    data_file = [repo_dir fileslash 'data' fileslash  'UDS.db'];
    conn = sqlite(data_file);
    
    sqlquery = "SELECT bus, long, lat, feeder, substation, taz FROM buses where type = 'urban'";
    bus_data = fetch(conn,sqlquery);
    sqlquery = "SELECT tazce10,x,y  FROM taz";
    taz_data = fetch(conn,sqlquery);
    sqlquery = "SELECT Name, long, lat, TAZ FROM substations";
    substation_data = fetch(conn,sqlquery);
    
    % Add TAZ Shape Data
    taz_shape = matfile([data_file(1:end-6) 'TAZ_Shapes.mat']);
    taz_shape = taz_shape.Data;
    taz_shape = struct2table(taz_shape);
    
    taz_data = [taz_data(:,1),taz_shape(:,1),taz_data(:,2:end)];
    taz_data = renamevars(taz_data,"tazce10", "Name");
end

%% Determine Overload Buses
function [bus_overloads,transformer_overloads_new,line_overloads_new,other_components_overloads_new] = find_overloaded_buses(overload_data)
    % Read data from overload file
    elements = overload_data(2:end,1);
    
    % All Elements have one of these three Identfiers before bus name
    bus_identifiers = [{'(R:'}, {'Transformer.SB'}, {'Line.SB'}];
    line_overloads_new = 0;
    transformer_overloads_new = 0;
    other_components_overloads_new = 0;
    
    for x = 1:length(elements)
        current_element = elements{x};
        
        % Determine Bus Name
        if contains(current_element, bus_identifiers(1),'IgnoreCase',true)
            ind = strfind(current_element,bus_identifiers(1));
            current_bus = current_element(ind+3:end);
            [current_bus,~] = strtok(current_bus,')');           
            % These elements are between/contain 2 buses
            [bus1, bus2] = strtok(current_bus,'-');
            current_bus = [{bus1}; {bus2(2:end)}];
            if contains(current_element, {'Line.L'},'IgnoreCase',true)
                line_overloads_new = line_overloads_new + 1;
            elseif contains(current_element, {'Transformer.TR'},'IgnoreCase',true)
                transformer_overloads_new = transformer_overloads_new + 1;
            else
                other_components_overloads_new = other_components_overloads_new + 1;
            end
        elseif contains(current_element, bus_identifiers(2),'IgnoreCase',true)
            ind = strfind(current_element,'_');
            current_bus = current_element(ind(1)+1:ind(3)-1);
            transformer_overloads_new = transformer_overloads_new + 1;
        elseif contains(current_element, bus_identifiers(3),'IgnoreCase',true)
            ind = strfind(current_element,'_');
            current_bus = current_element(ind(1)+1:ind(3)-1);
            line_overloads_new = line_overloads_new + 1;
        end

        % Create Table of Bus Names and # of Overloads
        if ischar(current_bus)
            if x == 1
                buses = [{current_bus}, {1}];
                continue
            end
            if any(strcmpi(buses(:,1),current_bus))
                ind = strcmpi(buses(:,1),current_bus);
                buses(ind,2) = num2cell(buses{ind,2} + 1);
            else
                buses = [buses; {current_bus}, {1}];
            end
        else        
            y = 1;
                if x == 1 && y == 1
                    buses = [current_bus(y), {1}];                  
                    continue
                end                
                if any(strcmp(buses(:,1),current_bus(y)))
                    ind = strcmp(buses(:,1),current_bus(y));
                    buses(ind,2) = num2cell(buses{ind,2} + 1);
                else
                    buses = [buses; current_bus(y), {1}];
                end
        end
    end

    % Output as Table
    bus_overloads = cell2table(buses, "VariableNames",["Name" "Overloads"]);
end

%% Compute Total Overloads in each TAZ
function [taz_data] = find_taz_overloads(bus_overloads,bus_data,substation_data,taz_data,interval)

    % Add column to taz_data to include overloads
    overload_interval = ['Overloads ' num2str(interval)];
    taz_data = [taz_data, table(zeros(size(taz_data,1),1),'VariableNames',{overload_interval})];
    
    for i = 1:height(bus_overloads)
        % For debuggin to monitor progress
        %if mod(i,250) == 0
        %    disp([num2str(100*i/height(bus_overloads)) '% done'])
        %end
    
        bus_ind = find(strcmpi(bus_data.bus,bus_overloads.Name(i)));
        if isempty(bus_ind)
            overloaded_bus = bus_overloads.Name(i); overloaded_bus = overloaded_bus{1};
            if convertCharsToStrings(overloaded_bus(end-3:end)) == "1247" 
                substation_ind = find(strcmpi(substation_data.Name,[overloaded_bus(1:end-4) '69']));
                current_taz = num2str(substation_data.TAZ(substation_ind));
            else
                substation_ind = find(strcmpi(substation_data.Name,bus_overloads.Name(i)));
                current_taz = num2str(substation_data.TAZ(substation_ind));
            end
        else
            current_taz = num2str(bus_data.taz(bus_ind));
        end
        taz_ind = find(strcmpi(taz_data.Name,current_taz));
        taz_data.(overload_interval)(taz_ind) = taz_data.(overload_interval)(taz_ind) + bus_overloads.Overloads(i);
    end
end

%% Plotting
function [] = plotData(gx,taz_data, interval)
    cla(gx);
    overload_interval = ['Overloads ' num2str(interval)];
    taz_shape = [taz_data(:,"Shape"), taz_data(:,overload_interval)];
    geoplot(gx,taz_shape,ColorVariable=overload_interval,FaceAlpha=0.3,FaceColor='flat');
    a = colorbar;
    ylabel(a,'Overloads')
    title(gx,['Overloads by TAZ at Time = ' num2str(interval)])

    for i = 1:106
       hold on
       if taz_data.(overload_interval)(i) == 0
           %marker_size = min_marker; 
           geoplot(gx,taz_data.y(i),taz_data.x(i), 'g*','MarkerSize',7)        
       else
           %marker_size = min_marker + taz_data.Overloads(i)/20;
           geoplot(gx,taz_data.y(i),taz_data.x(i), 'r*','MarkerSize',7) 
       end
       txt = [ taz_data.Name(i), ' ', num2str(taz_data.(overload_interval)(i))];
       text(gx,taz_data.y(i),taz_data.x(i),txt,'FontSize',5,'HorizontalAlignment','center');
    end
end